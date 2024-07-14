"""Client for communication with LetMeKnow."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from socket import gaierror
from typing import TYPE_CHECKING, Any

from aiohttp import (
    ClientConnectionError,
    ClientSession,
    ClientWebSocketResponse,
    WSMsgType,
    WSServerHandshakeError,
)
from yarl import URL

from .const import LOGGER, TARGETS_ALL_CLIENTS, VERSION
from .exceptions import LMKConnectionError, LMKNotConnectedError
from .models import (
    LMKClientType,
    LMKNotification,
    LMKWSNotification,
    LMKWSRegister,
    LMKWSRequestType,
    LMKWSResponseError,
    LMKWSResponseSuccess,
    LMKWSResponseType,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Self


@dataclass
class LMKClient:
    """Client to communicate with LetMeKnow."""

    lmk_host: str
    lmk_port: int
    lmk_client_type: LMKClientType
    lmk_user_id: str

    session: ClientSession | None = None
    request_timeout: int = 10
    _close_session: bool = False
    _ws: ClientWebSocketResponse | None = None

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The LMKClient object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self._close()

    async def _close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def _ws_send(
        self,
        data: dict[str, Any],
        wait_for_response: bool | None = None,
    ) -> LMKWSResponseSuccess | LMKWSResponseError:
        """Send data to the websocket server.

        Args:
        ----
            data: Data to send.
            wait_for_response: Wait for a response. Defaults to True.

        """
        if self._ws is None or self._ws.closed:
            raise LMKNotConnectedError

        # Default to waiting for a response
        if wait_for_response is None:
            wait_for_response = True

        LOGGER.debug("Sending data to websocket server: %s", data)

        try:
            await self._ws.send_json(data)
        except (
            ClientConnectionError,
            ConnectionResetError,
            gaierror,
        ) as error:
            raise LMKConnectionError from error

        if not wait_for_response:
            return LMKWSResponseSuccess(
                type=LMKWSResponseType.SUCCESS,
                succeeded=True,
                message="No response expected",
            )

        async with asyncio.timeout(self.request_timeout):
            response = await self._ws.receive()

        if response.type == WSMsgType.TEXT:
            # Get the response data
            response_data: dict[str, Any] = response.json()

            if "error" in response_data:
                return LMKWSResponseError.from_dict(response_data)

            return LMKWSResponseSuccess.from_dict(response_data)

        if response.type in (
            WSMsgType.CLOSE,
            WSMsgType.CLOSED,
            WSMsgType.CLOSING,
        ):
            self._ws = None
            return LMKWSResponseError(
                type=LMKWSResponseType.ERROR,
                message="Connection closed",
                error="Connection closed",
            )

        return LMKWSResponseError(
            type=LMKWSResponseType.ERROR,
            message="Unused response type",
            error=response.type.name,
        )

    @property
    def ws_connected(self) -> bool:
        """Check if the websocket is connected.

        Returns
        -------
            True if the websocket is connected.

        """
        return self._ws is not None and not self._ws.closed

    async def ws_connect(self) -> bool:
        """Connect to LetMeKnow websocket server.

        Returns
        -------
            True if the connection was successful.

        """
        url = URL.build(
            scheme="ws",
            host=self.lmk_host,
            port=self.lmk_port,
        ).joinpath("websocket")

        LOGGER.debug("Connecting to websocket server: %s", url)

        headers = {
            "User-Agent": f"LMKClientPy/{VERSION}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                self._ws = await self.session.ws_connect(
                    url=url,
                    headers=headers,
                    heartbeat=30,
                )
        except (
            asyncio.TimeoutError,
            WSServerHandshakeError,
            ClientConnectionError,
            gaierror,
        ) as error:
            raise LMKConnectionError from error

        return True

    async def ws_keep_alive(self) -> None:
        """Keep the websocket connection alive."""
        while self.ws_connected:
            await asyncio.sleep(10)

        LOGGER.info("Websocket connection closed, reconnecting")

        if not await self.ws_connect():
            LOGGER.error("Failed to reconnect to websocket server")
            return

        if (
            register_response := await self.ws_register()
        ).type != LMKWSResponseType.REGISTER:
            LOGGER.error(
                "Failed to register with websocket server: %s", register_response
            )
            return

        LOGGER.info("Reconnected to websocket server")

        # Continue to keep the connection alive
        await self.ws_keep_alive()

    async def ws_register(self) -> LMKWSResponseSuccess | LMKWSResponseError:
        """Register with the websocket server.

        Returns
        -------
            The response from the websocket server.

        """
        LOGGER.debug("Registering with the websocket server as: %s", self.lmk_user_id)

        return await self._ws_send(
            LMKWSRegister(
                type=LMKWSRequestType.REGISTER,
                user_id=self.lmk_user_id,
            ).to_dict()
        )

    async def ws_send_notification(
        self,
        notification: LMKNotification,
        targets: list[str] | None = None,
    ) -> LMKWSResponseSuccess | LMKWSResponseError:
        """Send a notification to the websocket server.

        Args:
        ----
            notification: Notification to send.
            targets: List of targets to send to. Defaults to all clients.

        Returns:
        -------
            The response from the websocket server.

        """
        if targets is None:
            targets = TARGETS_ALL_CLIENTS

        LOGGER.debug("Sending notification to the websocket server: %s", notification)
        LOGGER.debug("Notification targets: %s", targets)

        return await self._ws_send(
            LMKWSNotification(
                type=LMKWSRequestType.NOTIFICATION,
                data=notification,
                targets=targets,
            ).to_dict()
        )

    async def ws_listen_for_notifications(
        self,
        cb: Callable[[LMKNotification], None],
    ) -> None:
        """Listen for notifications.

        Args:
        ----
            cb: Callback to call when a notification is received.

        """
        if self._ws is None or self._ws.closed:
            raise LMKNotConnectedError

        async for message in self._ws:
            if message.type == 1:
                response_data: dict[str, Any] = message.json()
                notification = LMKWSNotification.from_dict(response_data)
                cb(notification.data)
            else:
                break

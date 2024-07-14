"""Example file for connecting to the LetMeKnow websocket server."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import logging
from typing import Final

from letmeknowclient import (
    LMKClient,
    LMKClientType,
    LMKNotification,
    LMKNotificationImage,
    LMKWSResponseType,
    generate_user_id,
)

CLIENT_TYPE: Final[LMKClientType] = LMKClientType.HEADLESS


@dataclass(slots=True)
class Args:
    """Arguments for the example."""

    host: str = "localhost"
    port: int = 8080
    title: str | None = None
    subtitle: str | None = None
    content: str | None = None
    image: str | None = None


def interpret_args() -> Args:
    """Interpret the arguments from the command line.

    Returns
    -------
        Args: The arguments.

    """
    # Parse arguments from the command line
    parser = argparse.ArgumentParser(description="Example for LetMeKnow")
    parser.add_argument("--host", default="localhost", help="Host of the server")
    parser.add_argument("--port", default=8080, help="Port of the server")
    parser.add_argument("--title", default=None, help="Title of the notification")
    parser.add_argument("--subtitle", default=None, help="Subtitle of the notification")
    parser.add_argument("--content", default=None, help="Content of the notification")
    parser.add_argument("--image", default=None, help="Image of the notification")
    args = parser.parse_args()

    return Args(
        host=args.host,
        port=args.port,
        title=args.title,
        subtitle=args.subtitle,
        content=args.content,
        image=args.image,
    )


async def run() -> None:
    """Run the example.

    This function connects to the LetMeKnow server and sends a notification.

    """
    args = interpret_args()

    async with LMKClient(
        lmk_client_type=CLIENT_TYPE,
        lmk_host=args.host,
        lmk_port=args.port,
        lmk_user_id=generate_user_id(CLIENT_TYPE),
    ) as lmk_client:
        if not await lmk_client.ws_connect():
            logging.fatal("Could not connect to the server")
            return

        # Register with the server
        register_response = await lmk_client.ws_register()
        if register_response.type != LMKWSResponseType.REGISTER:
            logging.fatal("Could not register with the server: %s", register_response)
            return

        logging.info("Registered with the server: %s", register_response)

        # Create the notification
        notification = LMKNotification(
            type="notification",
            title=args.title,
            subtitle=args.subtitle,
            content=args.content,
            image=LMKNotificationImage(url=args.image) if args.image else None,
        )
        logging.info("Created notification: %s", notification)

        # Send the notification
        notification_response = await lmk_client.ws_send_notification(notification)
        if notification_response.type != LMKWSResponseType.NOTIFICATION_SENT:
            logging.fatal("Could not send the notification: %s", notification_response)
            return

        logging.info("Sent notification: %s", notification_response)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )

    logging.getLogger("asyncio").setLevel(logging.INFO)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())

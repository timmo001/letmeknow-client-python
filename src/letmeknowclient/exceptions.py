"""Exceptions for LetMeKnow."""

from __future__ import annotations


class LMKError(Exception):
    """LetMeKnow Generic exception."""

    def __init__(self, message: str | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message or "An unknown error occurred")


class LMKConnectionError(LMKError):
    """LetMeKnow connection exception."""

    def __init__(
        self,
        connection_type: str = "WebSocket",
    ) -> None:
        """Initialize the exception."""
        super().__init__(f"Error connecting to {connection_type}")


class LMKNotConnectedError(LMKError):
    """LetMeKnow not connected exception."""

    def __init__(
        self,
        connection_type: str = "WebSocket",
    ) -> None:
        """Initialize the exception."""
        super().__init__(f"{connection_type} connection not established")

"""Python client for LetMeKnow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Self


class LMKClientType(StrEnum):
    """Enum of client type."""

    CLIENT = "client"
    HEADLESS = "headless"


@dataclass(slots=True)
class LMKNotification:
    """Notification."""

    type: str | None = None
    title: str | None = None
    subtitle: str | None = None
    content: str | None = None
    image: LMKNotificationImage | None = None
    timeout: int | None = None

    @classmethod
    def from_dict(cls, result: dict[str, Any]) -> Self:
        """Initialize from a dict."""
        return cls(
            type=result.get("type"),
            title=result.get("title"),
            subtitle=result.get("subtitle"),
            content=result.get("content"),
            image=LMKNotificationImage.from_dict(result["image"])
            if result.get("image")
            else None,
            timeout=result.get("timeout"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert class to a dict."""
        return {
            "type": str(self.type),
            "title": self.title,
            "subtitle": self.subtitle,
            "content": self.content,
            "image": self.image.to_dict() if self.image else None,
            "timeout": self.timeout,
        }


@dataclass(slots=True)
class LMKNotificationImage:
    """Notification image."""

    url: str

    @classmethod
    def from_dict(cls, result: dict[str, Any]) -> Self:
        """Initialize from a dict."""
        return cls(
            url=result["url"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert class to a dict."""
        return {
            "url": self.url,
        }


class LMKWSRequestType(StrEnum):
    """Enum of websocket request type."""

    REGISTER = "register"
    NOTIFICATION = "notification"


class LMKWSResponseType(StrEnum):
    """Enum of websocket response type."""

    ERROR = "error"
    NOTIFICATION_SENT = "notificationSent"
    REGISTER = "register"
    SUCCESS = "success"  # Generic success response, not sent by the server


@dataclass(slots=True)
class LMKWSRegister:
    """Websocket register client."""

    type: LMKWSRequestType
    user_id: str

    @classmethod
    def from_dict(cls, result: dict[str, Any]) -> Self:
        """Initialize from a dict."""
        return cls(
            type=LMKWSRequestType(result["type"]),
            user_id=result["userID"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert class to a dict."""
        return {
            "type": str(self.type),
            "userID": self.user_id,
        }


@dataclass(slots=True)
class LMKWSNotification:
    """Websocket notification."""

    type: LMKWSRequestType
    data: LMKNotification
    targets: list[str]

    @classmethod
    def from_dict(cls, result: dict[str, Any]) -> Self:
        """Initialize from a dict."""
        return cls(
            type=LMKWSRequestType(result["type"]),
            data=LMKNotification.from_dict(result["data"]),
            targets=result["targets"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert class to a dict."""
        return {
            "type": str(self.type),
            "data": self.data.to_dict(),
            "targets": self.targets,
        }


@dataclass(slots=True)
class LMKWSResponseError:
    """Websocket response error."""

    type: LMKWSResponseType
    message: str
    error: str

    @classmethod
    def from_dict(cls, result: dict[str, Any]) -> Self:
        """Initialize from a dict."""
        return cls(
            type=LMKWSResponseType(result["type"]),
            message=result["message"],
            error=result["error"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert class to a dict."""
        return {
            "type": str(self.type),
            "message": self.message,
            "error": self.error,
        }


@dataclass(slots=True)
class LMKWSResponseSuccess:
    """Websocket response success."""

    type: LMKWSResponseType
    succeeded: bool
    message: str

    @classmethod
    def from_dict(cls, result: dict[str, Any]) -> Self:
        """Initialize from a dict."""
        return cls(
            type=LMKWSResponseType(result["type"]),
            succeeded=result["succeeded"],
            message=result["message"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert class to a dict."""
        return {
            "type": str(self.type),
            "succeeded": self.succeeded,
            "message": self.message,
        }

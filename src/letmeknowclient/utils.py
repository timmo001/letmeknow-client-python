"""Utility functions for the LetMeKnow."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .models import LMKClientType


def generate_user_id(client_type: LMKClientType) -> str:
    """Generate a user ID."""
    return f"{client_type}-{uuid4()!s}"

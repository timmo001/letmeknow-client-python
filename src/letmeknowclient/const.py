"""Constants for LetMeKnow."""

from __future__ import annotations

from importlib import metadata
import logging
from typing import Final

LOGGER = logging.getLogger(__package__)
VERSION: Final[str] = metadata.version(__package__)

TARGETS_ALL: Final[list[str]] = []
TARGETS_ALL_CLIENTS: Final[list[str]] = ["client-*"]
TARGETS_ALL_HEADLESS: Final[list[str]] = ["headless-*"]

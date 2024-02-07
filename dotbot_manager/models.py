"""Pydantic models used by the controller and server application."""

from enum import IntEnum
from typing import List, Optional, Union

from pydantic import BaseModel


class DotBotManagerIdentity(BaseModel):
    """Simple model to hold a DotBot Manager identity."""

    id: str

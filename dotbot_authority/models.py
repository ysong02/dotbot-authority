"""Pydantic models used by the controller and server application."""

from enum import IntEnum
from typing import List, Optional, Union

from pydantic import BaseModel


class DotBotNotificationCommand(IntEnum):
    """Notification command of a DotBot."""

    NONE: int = 0
    AUTHORIZATION_RESULT: int = 1
    ATTESTATION_RESULT: int = 2


class DotBotAuthorityIdentity(BaseModel):
    """Simple model to hold a DotBot Authority identity."""

    id: str


class AuthorizationResult(BaseModel):
    timestamp: int
    id: int
    authorized: bool


class AttestationResult(BaseModel):
    id: str
    attestation_result: bool
    software_name: str
    fs_name: str
    fs_size: int
    tag_version: int



class DotBotNotificationModel(BaseModel):
    """Model class used to send notifications."""

    cmd: DotBotNotificationCommand
    data: Optional[Union[AuthorizationResult, AttestationResult]] = None

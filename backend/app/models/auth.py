from typing import Literal

from pydantic import BaseModel


class MagicLinkRequest(BaseModel):
    email: str


class MagicLinkAcceptedResponse(BaseModel):
    status: Literal["accepted"]
    message: str


class MagicLinkConfirmation(BaseModel):
    token: str

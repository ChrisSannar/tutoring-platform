from typing import Literal

from pydantic import BaseModel


class LoginRequestResponse(BaseModel):
    id: str
    email: str
    requested_at: str
    status: Literal["pending", "generated"]


class LoginRequestListResponse(BaseModel):
    login_requests: list[LoginRequestResponse]


class GeneratedLoginLinkResponse(BaseModel):
    magic_link: str

from typing import Literal

from pydantic import BaseModel


class PilotDataDeletionRequest(BaseModel):
    confirmation: str


class RemovedPilotDataResponse(BaseModel):
    invitations: int
    student_sessions: int
    bookings: int


class PilotDataDeletionResponse(BaseModel):
    status: Literal["deleted"]
    removed: RemovedPilotDataResponse

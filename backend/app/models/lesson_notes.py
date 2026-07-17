from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LessonNoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(max_length=200)
    markdown_source: str

    @field_validator("title")
    @classmethod
    def visible_title(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("title must contain text")
        return value

    @field_validator("markdown_source")
    @classmethod
    def bounded_source(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 100 * 1024:
            raise ValueError("Markdown source exceeds 100 KB")
        return value


class LessonNoteResponse(LessonNoteInput):
    id: str
    booking_id: str
    status: Literal["draft", "published"]


class SharedLessonNote(LessonNoteResponse):
    status: Literal["published"]
    booking_date: date


class SharedLessonNoteList(BaseModel):
    lesson_notes: list[SharedLessonNote]


class ConfirmedLessonNoteDeletion(BaseModel):
    confirmed: Literal[True]


class TutorLessonNoteWorkspaceItem(BaseModel):
    booking_id: str
    booking_date: date
    note: LessonNoteResponse | None

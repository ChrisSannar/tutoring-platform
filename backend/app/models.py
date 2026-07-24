from datetime import date, datetime, time
import re
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class MagicLinkRequest(BaseModel):
    email: str


class MagicLinkAcceptedResponse(BaseModel):
    status: Literal["accepted"]
    message: str


class MagicLinkConfirmation(BaseModel):
    token: str


class AvailabilityWindowInput(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def valid_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must precede end_time")
        return self


class AvailabilityWindowResponse(AvailabilityWindowInput):
    id: str


class BlockedTimeInput(BaseModel):
    start_at: datetime
    end_at: datetime
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def valid_range(self):
        if self.start_at >= self.end_at:
            raise ValueError("start_at must precede end_at")
        return self


class BlockedTimeResponse(BlockedTimeInput):
    id: str


class BookableSlot(BaseModel):
    start_at: datetime
    end_at: datetime


class BookableSlotList(BaseModel):
    tutor_timezone: str
    slots: list[BookableSlot]


class TutorOverrideInput(BaseModel):
    start_at: datetime
    warning: str = Field(min_length=1, max_length=500)


class TutorOverrideResponse(TutorOverrideInput):
    id: str
    end_at: datetime
    requires_booking_warning: bool


class StudentBookingInput(BaseModel):
    start_at: datetime
    focus: str | None = Field(default=None, max_length=500)
    confirmed: Literal[True]


class ComplimentaryBookingInput(BaseModel):
    start_at: datetime
    focus: str | None = Field(default=None, max_length=500)
    complimentary: Literal[True]
    override_id: str | None = None
    warning_acknowledged: bool = False


class BookingResponse(BaseModel):
    id: str
    start_at: datetime
    end_at: datetime
    duration_minutes: Literal[60]
    tutor_timezone: str
    funding_kind: Literal["first_session_promotion", "session_credit", "complimentary", "paid"]
    focus: str | None
    meeting_details: str | None
    price_cents: int
    currency: Literal["USD"]
    status: Literal["upcoming", "completed", "cancelled"]


class MeetingDetailsUpdate(BaseModel):
    meeting_details: str | None = Field(default=None, max_length=5000)


class TutorBookingMove(BaseModel):
    start_at: datetime
    override_id: str | None = None
    warning_acknowledged: bool = False


class StudentBookingMove(BaseModel):
    start_at: datetime


class StudentBookingCancellation(BaseModel):
    forfeit_funding: bool


class BookingStudent(BaseModel):
    id: str
    display_name: str
    email: str


class TutorCalendarBooking(BookingResponse):
    student: BookingStudent


class TutorCalendarResponse(BaseModel):
    bookings: list[TutorCalendarBooking]


class CheckoutInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_at: datetime
    focus: str | None = Field(default=None, max_length=500)


class CheckoutResponse(BaseModel):
    checkout_session_id: str
    checkout_url: str
    amount_cents: int
    currency: Literal["USD"]
    status: Literal["pending", "fulfilled", "expired", "mismatch"]


class CreditAdjustmentRequest(BaseModel):
    quantity: int
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("quantity")
    @classmethod
    def require_nonzero_quantity(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity must not be zero")
        return value

    @field_validator("reason")
    @classmethod
    def require_visible_reason(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("reason must contain text")
        return normalized


class CreditBalanceResponse(BaseModel):
    session_credits: int


class CreditLedgerEventResponse(BaseModel):
    id: str
    event_type: str
    quantity: int
    reason: str | None
    created_at: datetime


class CreditLedgerResponse(BaseModel):
    events: list[CreditLedgerEventResponse]


class InquirySubmission(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("email")
    @classmethod
    def normalize_valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must be valid")
        return normalized

    @field_validator("message")
    @classmethod
    def require_context(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must contain text")
        return normalized


class InquiryAcceptedResponse(BaseModel):
    message: str


class TutorInquiryResponse(BaseModel):
    id: str
    email: str
    message: str
    status: Literal["new", "invited"]
    invitation_id: str | None = None


class TutorInquiryListResponse(BaseModel):
    inquiries: list[TutorInquiryResponse]


class InquiryDeletionConfirmation(BaseModel):
    confirmed: Literal[True]


class DirectInvitationClaimRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)

    @field_validator("display_name")
    @classmethod
    def require_visible_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display name must contain text")
        return normalized


class StudentFundingResponse(BaseModel):
    first_session_promotion: Literal["available", "unavailable"]
    session_credits: int


class ClaimedInvitationResponse(BaseModel):
    status: Literal["claimed"]
    role: Literal["student"]
    email: str
    display_name: str
    csrf_token: str


class ManualInvitationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str

    @field_validator("email")
    @classmethod
    def normalize_valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("email must be valid")
        return normalized


class CreatedInvitationResponse(BaseModel):
    id: str
    email: str
    status: Literal["created"]
    invitation_url: str
    expires_at: datetime


class InvitationLinkChangeResponse(BaseModel):
    id: str
    status: Literal["created"]
    invitation_url: str
    expires_at: datetime


class InvitationLinkResponse(BaseModel):
    invitation_url: str


class TutorInvitationRecordResponse(BaseModel):
    id: str
    email: str
    display_name: str
    shared_personal_message: str
    private_tutor_note: str
    status: Literal["created", "opened", "claimed", "revoked", "expired"]
    created_at: datetime | None
    first_opened_at: datetime | None
    claimed_at: datetime | None
    expired_at: datetime | None
    revoked_at: datetime | None
    expires_at: datetime | None


class InviteeInvitationResponse(BaseModel):
    email: str


class InvitationEmailCorrectionRequest(BaseModel):
    email: str


class CorrectedInvitationResponse(BaseModel):
    id: str
    email: str
    status: Literal["created", "opened"]


class RevokedInvitationResponse(BaseModel):
    id: str
    status: Literal["revoked"]


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


class LoginRequestResponse(BaseModel):
    id: str
    email: str
    requested_at: str
    status: Literal["pending", "generated"]


class LoginRequestListResponse(BaseModel):
    login_requests: list[LoginRequestResponse]


class GeneratedLoginLinkResponse(BaseModel):
    magic_link: str


class PilotDataDeletionRequest(BaseModel):
    confirmation: str


class RemovedPilotDataResponse(BaseModel):
    invitations: int
    student_sessions: int
    bookings: int


class PilotDataDeletionResponse(BaseModel):
    status: Literal["deleted"]
    removed: RemovedPilotDataResponse


class RefundRequestResponse(BaseModel):
    id: str
    booking_id: str
    amount_cents: int
    currency: Literal["USD"]
    status: Literal["pending", "declined", "refunded"]
    created_at: datetime


class RefundStudent(BaseModel):
    id: str
    display_name: str


class TutorRefundRequestResponse(RefundRequestResponse):
    student: RefundStudent


class StudentRefundList(BaseModel):
    refund_requests: list[RefundRequestResponse]


class TutorRefundList(BaseModel):
    refund_requests: list[TutorRefundRequestResponse]


class TutorStudentResponse(BaseModel):
    id: str
    email: str
    display_name: str


class TutorStudentListResponse(BaseModel):
    students: list[TutorStudentResponse]


class StudentFundingSummary(BaseModel):
    first_session_promotion: Literal["available", "unavailable"]
    session_credits: int


class TutorStudentDetailResponse(TutorStudentResponse):
    funding: StudentFundingSummary
    pending_refund_requests: list[dict[str, str]]
    upcoming_booking: dict[str, str] | None


class TutorSettingsUpdate(BaseModel):
    currency: Literal["USD"]
    session_price_cents: int = Field(gt=0, le=1_000_000)
    tutor_timezone: str
    default_meeting_details: str | None = Field(default=None, max_length=5000)

    @field_validator("tutor_timezone")
    @classmethod
    def require_iana_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("tutor_timezone must be an IANA timezone") from error
        return value


class TutorSettingsResponse(TutorSettingsUpdate):
    pass

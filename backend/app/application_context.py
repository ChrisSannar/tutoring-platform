from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from app.config import Settings, get_settings


@dataclass
class ApplicationContext:
    settings: Settings
    development_outbox: list[dict[str, str]] = field(default_factory=list)
    now: Callable[[], datetime] = field(default=lambda: datetime.now(timezone.utc))
    refund_payment: Callable[[str, int, str, str], tuple[bool, str | None]] | None = None

    @classmethod
    def build(cls) -> "ApplicationContext":
        settings = get_settings()
        context = cls(settings=settings)
        from app.refunds.provider import refund_payment
        context.refund_payment = lambda payment, amount, currency, key: refund_payment(
            settings.stripe_provider_mode, settings.stripe_secret_key.get_secret_value(), payment, amount, currency, key
        )
        return context

    @property
    def session_cookie_name(self) -> str:
        if self.settings.environment == "production":
            return "__Host-tutoring_session"
        return "tutoring_session"

    @property
    def csrf_cookie_name(self) -> str:
        if self.settings.environment == "production":
            return "__Host-tutoring_csrf"
        return "tutoring_csrf"

    @property
    def secure_cookies(self) -> bool:
        return self.settings.environment == "production"

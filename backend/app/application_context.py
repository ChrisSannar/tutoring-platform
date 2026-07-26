from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from app.config import Settings, get_settings


@dataclass
class ApplicationContext:
    settings: Settings
    development_outbox: list[dict[str, str]] = field(default_factory=list)
    now: Callable[[], datetime] = field(default=lambda: datetime.now(timezone.utc))

    @classmethod
    def build(cls) -> "ApplicationContext":
        return cls(settings=get_settings())

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

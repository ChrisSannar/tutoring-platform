from app.authentication.magic_links import issue_magic_link, magic_link_is_active
from app.authentication.rate_limits import accept_magic_link_request
from app.authentication.session_creation import consume_magic_link
from app.authentication.session_queries import active_session, student_session_details
from app.authentication.session_security import revoke_session, session_authorizes_mutation

__all__ = [
    "accept_magic_link_request",
    "active_session",
    "consume_magic_link",
    "issue_magic_link",
    "magic_link_is_active",
    "revoke_session",
    "session_authorizes_mutation",
    "student_session_details",
]

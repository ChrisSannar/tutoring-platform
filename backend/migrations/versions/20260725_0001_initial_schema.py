"""Establish the initial schema authority (squashed)."""

from alembic import op

revision = "20260725_0001"
down_revision = None
branch_labels = None
depends_on = None


TABLES = [
    "lesson_notes",
    "booking_change_receipts",
    "bookings",
    "tutor_overrides",
    "blocked_times",
    "availability_windows",
    "login_requests",
    "tutor_settings",
    "credit_ledger_entries",
    "invitations",
    "inquiries",
    "authentication_request_events",
    "authentication_sessions",
    "magic_link_tokens",
    "accounts",
]


def upgrade() -> None:
    op.execute("""
CREATE TABLE accounts (
	id VARCHAR(36) NOT NULL,
	email VARCHAR(320) NOT NULL,
	role VARCHAR(16) NOT NULL, display_name VARCHAR(200),
	PRIMARY KEY (id),
	UNIQUE (email)
)""")
    op.execute("""
CREATE TABLE magic_link_tokens (
	id VARCHAR(36) NOT NULL,
	account_id VARCHAR(36) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	expires_at DATETIME NOT NULL,
	consumed_at DATETIME,
	PRIMARY KEY (id),
	FOREIGN KEY(account_id) REFERENCES accounts (id),
	UNIQUE (token_hash)
)""")
    op.execute("""
CREATE TABLE authentication_sessions (
	id VARCHAR(36) NOT NULL,
	account_id VARCHAR(36) NOT NULL,
	session_hash VARCHAR(64) NOT NULL,
	csrf_hash VARCHAR(64) NOT NULL,
	inactive_expires_at DATETIME NOT NULL,
	absolute_expires_at DATETIME NOT NULL,
	revoked_at DATETIME,
	PRIMARY KEY (id),
	FOREIGN KEY(account_id) REFERENCES accounts (id),
	UNIQUE (session_hash)
)""")
    op.execute("""
CREATE TABLE authentication_request_events (
	id VARCHAR(36) NOT NULL,
	email_hash VARCHAR(64) NOT NULL,
	ip_hash VARCHAR(64) NOT NULL,
	requested_at DATETIME NOT NULL,
	PRIMARY KEY (id)
)""")
    op.execute("""
CREATE TABLE inquiries (
	id VARCHAR(36) NOT NULL,
	email VARCHAR(320) NOT NULL,
	message TEXT NOT NULL,
	status VARCHAR(16) NOT NULL,
	submitted_ip_hash VARCHAR(64) NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id)
)""")
    op.execute("CREATE INDEX ix_inquiries_created_at ON inquiries (created_at)")
    op.execute("""
CREATE TABLE credit_ledger_entries (
	id VARCHAR(36) NOT NULL,
	student_account_id VARCHAR(36) NOT NULL,
	event_type VARCHAR(32) NOT NULL,
	quantity INTEGER NOT NULL,
	reason VARCHAR(500),
	idempotency_key VARCHAR(200) NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(student_account_id) REFERENCES accounts (id),
	UNIQUE (idempotency_key)
)""")
    op.execute("""
CREATE TABLE tutor_settings (
	id INTEGER NOT NULL,
	tutor_timezone VARCHAR(100) NOT NULL,
	default_meeting_details TEXT,
	PRIMARY KEY (id),
	CONSTRAINT ck_tutor_settings_singleton CHECK (id = 1)
)""")
    op.execute(
        "INSERT INTO tutor_settings (id, tutor_timezone) "
        "VALUES (1, 'America/Chicago')"
    )
    op.execute("""
CREATE TABLE login_requests (
	id VARCHAR(36) NOT NULL,
	account_id VARCHAR(36) NOT NULL,
	requested_at DATETIME NOT NULL,
	magic_link_token_id VARCHAR(36),
	dismissed_at DATETIME,
	PRIMARY KEY (id),
	FOREIGN KEY(account_id) REFERENCES accounts (id) ON DELETE CASCADE,
	FOREIGN KEY(magic_link_token_id) REFERENCES magic_link_tokens (id) ON DELETE SET NULL,
	UNIQUE (magic_link_token_id)
)""")
    op.execute("CREATE INDEX ix_login_requests_account ON login_requests (account_id)")
    op.execute("""
CREATE TABLE availability_windows (
	id VARCHAR(36) NOT NULL,
	weekday INTEGER NOT NULL,
	start_time VARCHAR(5) NOT NULL,
	end_time VARCHAR(5) NOT NULL,
	PRIMARY KEY (id),
	CHECK (weekday BETWEEN 0 AND 6),
	CHECK (start_time < end_time)
)""")
    op.execute("""
CREATE TABLE blocked_times (
	id VARCHAR(36) NOT NULL,
	start_at DATETIME NOT NULL,
	end_at DATETIME NOT NULL,
	reason VARCHAR(500),
	PRIMARY KEY (id),
	CHECK (start_at < end_at)
)""")
    op.execute("""
CREATE TABLE tutor_overrides (
	id VARCHAR(36) NOT NULL,
	start_at DATETIME NOT NULL,
	end_at DATETIME NOT NULL,
	warning VARCHAR(500) NOT NULL,
	PRIMARY KEY (id)
)""")
    op.execute("""
CREATE TABLE bookings (
	id VARCHAR(36) NOT NULL,
	student_account_id VARCHAR(36) NOT NULL,
	start_at DATETIME NOT NULL,
	end_at DATETIME NOT NULL,
	status VARCHAR(24) NOT NULL,
	funding_kind VARCHAR(24) NOT NULL,
	focus VARCHAR(500),
	meeting_details_snapshot TEXT,
	idempotency_key VARCHAR(200) NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(student_account_id) REFERENCES accounts (id),
	CHECK (status IN ('upcoming', 'past', 'cancelled')),
	CHECK (funding_kind IN ('session_credit', 'complimentary')),
	UNIQUE (idempotency_key)
)""")
    op.execute("""
CREATE TABLE booking_change_receipts (
	id VARCHAR(36) NOT NULL,
	booking_id VARCHAR(36) NOT NULL,
	kind VARCHAR(24) NOT NULL,
	idempotency_key VARCHAR(200) NOT NULL,
	created_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(booking_id) REFERENCES bookings (id),
	UNIQUE (idempotency_key)
)""")
    op.execute("""
CREATE TABLE lesson_notes (
	id VARCHAR(36) NOT NULL,
	booking_id VARCHAR(36) NOT NULL,
	title VARCHAR(200) NOT NULL,
	markdown_source TEXT NOT NULL,
	published_at DATETIME,
	deleted_at DATETIME,
	updated_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(booking_id) REFERENCES bookings (id),
	UNIQUE (booking_id)
)""")
    op.execute("""
CREATE TABLE "invitations" (
	id VARCHAR(36) NOT NULL,
	email VARCHAR(320) NOT NULL,
	display_name VARCHAR(200) NOT NULL,
	shared_personal_message TEXT NOT NULL,
	private_tutor_note TEXT NOT NULL,
	status VARCHAR(16) NOT NULL,
	token_hash VARCHAR(64),
	expires_at DATETIME,
	claimed_account_id VARCHAR(36),
	token_ciphertext BLOB,
	inquiry_id VARCHAR(36),
	created_at DATETIME,
	first_opened_at DATETIME,
	claimed_at DATETIME,
	expired_at DATETIME,
	revoked_at DATETIME,
	PRIMARY KEY (id),
	CONSTRAINT uq_invitations_inquiry_id UNIQUE (inquiry_id),
	CONSTRAINT uq_invitations_claimed_account_id UNIQUE (claimed_account_id),
	CONSTRAINT fk_invitations_inquiry_id FOREIGN KEY(inquiry_id) REFERENCES inquiries (id),
	CONSTRAINT fk_invitations_claimed_account_id FOREIGN KEY(claimed_account_id) REFERENCES accounts (id),
	CONSTRAINT ck_invitations_canonical_status CHECK (status IN ('created', 'opened', 'claimed', 'expired', 'revoked')),
	CONSTRAINT ck_invitations_opened_evidence CHECK (status != 'opened' OR first_opened_at IS NOT NULL OR created_at IS NULL),
	CONSTRAINT ck_invitations_claimed_evidence CHECK (status != 'claimed' OR (claimed_account_id IS NOT NULL AND (claimed_at IS NOT NULL OR created_at IS NULL))),
	CONSTRAINT ck_invitations_expired_evidence CHECK (status != 'expired' OR expired_at IS NOT NULL OR created_at IS NULL),
	CONSTRAINT ck_invitations_revoked_evidence CHECK (status != 'revoked' OR revoked_at IS NOT NULL OR created_at IS NULL),
	CONSTRAINT ck_invitations_terminal_tokens_erased CHECK (status NOT IN ('claimed', 'expired', 'revoked') OR (token_hash IS NULL AND token_ciphertext IS NULL)),
	UNIQUE (token_hash)
)""")


def downgrade() -> None:
    for table in TABLES:
        op.drop_table(table)

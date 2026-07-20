from datetime import datetime, timezone

from sqlalchemy import text


def utc_aware(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def occupied_intervals(
    connection,
    now: datetime,
    *,
    exclude_booking_id: str | None = None,
) -> list[tuple[datetime, datetime]]:
    rows = connection.execute(
        text(
            "SELECT start_at, end_at FROM blocked_times "
            "UNION ALL SELECT start_at, end_at FROM bookings "
            "WHERE status = 'upcoming' AND (:booking IS NULL OR id != :booking) "
            "UNION ALL SELECT start_at, end_at FROM slot_holds WHERE expires_at > :now"
        ),
        {"booking": exclude_booking_id, "now": utc_aware(now)},
    ).all()
    return [(utc_aware(row[0]), utc_aware(row[1])) for row in rows]


def interval_is_free(
    connection,
    start: datetime,
    end: datetime,
    now: datetime,
    *,
    exclude_booking_id: str | None = None,
) -> bool:
    start_at, end_at = utc_aware(start), utc_aware(end)
    return not any(
        start_at < busy_end and end_at > busy_start
        for busy_start, busy_end in occupied_intervals(
            connection, now, exclude_booking_id=exclude_booking_id
        )
    )

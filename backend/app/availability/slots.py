from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text

from app.occupancy import occupied_intervals, utc_aware

def local_datetime(day: date, value: str, zone: ZoneInfo) -> datetime:
    parsed = time.fromisoformat(value)
    return datetime.combine(day, parsed, zone)


def _derive_bookable_slots(
    connection, now: datetime, exclude_booking_id: str | None
) -> tuple[str, list[dict]]:
    now = utc_aware(now)
    timezone_name = connection.execute(
        text("SELECT tutor_timezone FROM tutor_settings WHERE id = 1")
    ).scalar_one()
    recurring = [
        dict(row)
        for row in connection.execute(
            text("SELECT weekday, start_time, end_time FROM availability_windows")
        ).mappings()
    ]
    zone = ZoneInfo(timezone_name)
    busy = occupied_intervals(
        connection, now, exclude_booking_id=exclude_booking_id
    )
    notice, horizon = now + timedelta(hours=24), now + timedelta(weeks=8)
    first_day = now.astimezone(zone).date()
    slots: list[dict] = []
    for offset in range(57):
        day = first_day + timedelta(days=offset)
        for window in recurring:
            if day.weekday() != window["weekday"]:
                continue
            cursor = local_datetime(day, window["start_time"], zone)
            end = local_datetime(day, window["end_time"], zone)
            while cursor + timedelta(hours=1) <= end:
                start_at = cursor.astimezone(timezone.utc)
                end_at = (cursor + timedelta(hours=1)).astimezone(timezone.utc)
                overlaps = any(start_at < busy_end and end_at > busy_start for busy_start, busy_end in busy)
                if start_at >= notice and end_at <= horizon and not overlaps:
                    slots.append({"start_at": start_at, "end_at": end_at})
                cursor += timedelta(hours=1)
    return timezone_name, slots


def derive_bookable_slots(
    database_url: str,
    now: datetime,
    *,
    connection=None,
    exclude_booking_id: str | None = None,
) -> tuple[str, list[dict]]:
    if connection is not None:
        return _derive_bookable_slots(connection, now, exclude_booking_id)
    engine = create_engine(database_url)
    try:
        with engine.connect() as opened_connection:
            return _derive_bookable_slots(
                opened_connection, now, exclude_booking_id
            )
    finally:
        engine.dispose()

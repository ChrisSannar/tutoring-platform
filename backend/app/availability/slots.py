from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text


def aware(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def conflicts(database_url: str, now: datetime) -> list[tuple[datetime, datetime]]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(text(
                "SELECT start_at, end_at FROM blocked_times UNION ALL "
                "SELECT start_at, end_at FROM bookings WHERE status = 'upcoming' UNION ALL "
                "SELECT start_at, end_at FROM slot_holds WHERE expires_at > :now"
            ), {"now": now}).all()
            return [(aware(row[0]), aware(row[1])) for row in rows]
    finally:
        engine.dispose()


def windows(database_url: str) -> tuple[str, list[dict]]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            timezone_name = connection.execute(text(
                "SELECT tutor_timezone FROM tutor_settings WHERE id = 1"
            )).scalar_one()
            rows = connection.execute(text(
                "SELECT weekday, start_time, end_time FROM availability_windows"
            )).mappings()
            return timezone_name, [dict(row) for row in rows]
    finally:
        engine.dispose()


def local_datetime(day: date, value: str, zone: ZoneInfo) -> datetime:
    parsed = time.fromisoformat(value)
    return datetime.combine(day, parsed, zone)


def derive_bookable_slots(database_url: str, now: datetime) -> tuple[str, list[dict]]:
    timezone_name, recurring = windows(database_url)
    zone, busy = ZoneInfo(timezone_name), conflicts(database_url, now)
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

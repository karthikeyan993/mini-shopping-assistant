"""The model has no clock. The harness knows the time, tells the model, and does all date arithmetic in code."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Bangkok")  # the customer's timezone, not the server's (servers run in UTC)

# A fixed vocabulary the model chooses from; code turns it into exact dates. LLMs are bad at date arithmetic.
PERIODS = ["today", "yesterday", "this_week", "last_week", "last_7_days", "last_30_days", "this_month", "last_month"]


def now() -> datetime:
    return datetime.now(TZ)


def header(t: datetime) -> str:
    """The line the system prompt carries on every request."""
    return (f"{t:%A %d %B %Y, %H:%M} (Asia/Bangkok, UTC+7). Thai dates may use the Buddhist Era: "
            f"{t.year} CE = {t.year + 543} BE.")


def resolve(period: str, t: datetime) -> tuple[datetime, datetime]:
    """Period name → [start, end) in Bangkok time. Weeks run Monday to Sunday.

    "last_week" means the previous calendar week (Mon–Sun), not the last 7 days; that's a product decision,
    so the answer always states the dates it used and the customer can correct it.
    """
    day0 = t.replace(hour=0, minute=0, second=0, microsecond=0)
    monday = day0 - timedelta(days=day0.weekday())
    first = day0.replace(day=1)
    if period == "today":
        return day0, day0 + timedelta(days=1)
    if period == "yesterday":
        return day0 - timedelta(days=1), day0
    if period == "this_week":
        return monday, day0 + timedelta(days=1)
    if period == "last_week":
        return monday - timedelta(days=7), monday
    if period == "last_7_days":
        return day0 - timedelta(days=6), day0 + timedelta(days=1)
    if period == "last_30_days":
        return day0 - timedelta(days=29), day0 + timedelta(days=1)
    if period == "this_month":
        return first, day0 + timedelta(days=1)
    if period == "last_month":
        prev_first = (first - timedelta(days=1)).replace(day=1)
        return prev_first, first
    raise ValueError(f"unknown period {period!r}")


def parse_date(s: str) -> datetime:
    """'2026-11-09' → midnight Bangkok time that day."""
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=TZ)


def describe(start: datetime, end: datetime) -> str:
    """[Mon 9 Nov, Mon 16 Nov) → 'Mon 9 Nov – Sun 15 Nov 2026'."""
    last = end - timedelta(days=1)
    if start.date() == last.date():
        return f"{start:%a} {start.day} {start:%b %Y}"
    return f"{start:%a} {start.day} {start:%b} – {last:%a} {last.day} {last:%b %Y}"


def to_utc_iso(t: datetime) -> str:
    """Orders are stored in UTC; convert range bounds before comparing, or late-evening orders land on the wrong day."""
    return t.astimezone(timezone.utc).isoformat(timespec="seconds")

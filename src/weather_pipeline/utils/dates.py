"""Date helpers."""

from collections.abc import Iterator
from datetime import date, timedelta


def month_chunks(start: date, end: date) -> Iterator[tuple[date, date]]:
    """Split a date range into calendar-month pieces.

    2026-01-15 to 2026-03-10 ->
        (2026-01-15, 2026-01-31), (2026-02-01, 2026-02-28), (2026-03-01, 2026-03-10)
    """
    chunk_start = start
    while chunk_start <= end:
        first_of_next_month = (chunk_start.replace(day=1) + timedelta(days=32)).replace(
            day=1
        )
        chunk_end = min(first_of_next_month - timedelta(days=1), end)
        yield chunk_start, chunk_end
        chunk_start = chunk_end + timedelta(days=1)

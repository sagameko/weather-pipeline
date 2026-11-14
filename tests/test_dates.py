from datetime import date

from weather_pipeline.utils.dates import month_chunks


def test_month_chunks_split_on_calendar_months():
    chunks = list(month_chunks(date(2026, 1, 15), date(2026, 3, 10)))
    assert chunks == [
        (date(2026, 1, 15), date(2026, 1, 31)),
        (date(2026, 2, 1), date(2026, 2, 28)),
        (date(2026, 3, 1), date(2026, 3, 10)),
    ]


def test_month_chunks_single_day():
    assert list(month_chunks(date(2026, 11, 1), date(2026, 11, 1))) == [
        (date(2026, 11, 1), date(2026, 11, 1))
    ]


def test_month_chunks_handles_december_and_leap_years():
    chunks = list(month_chunks(date(2027, 12, 20), date(2028, 2, 29)))
    assert chunks[0] == (date(2027, 12, 20), date(2027, 12, 31))
    assert chunks[-1] == (date(2028, 2, 1), date(2028, 2, 29))  # 2028 is a leap year

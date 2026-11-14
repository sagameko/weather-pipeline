import argparse
import logging
import sys
import time
from datetime import date, timedelta

from weather_pipeline.config import Settings, load_settings
from weather_pipeline.extract.weather_api import extract_all
from weather_pipeline.load.warehouse import load_all
from weather_pipeline.logging_setup import setup_logging
from weather_pipeline.transform.clean_weather import transform_all
from weather_pipeline.utils.dates import month_chunks

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    # The archive API publishes data with a delay of a few days, so stay a week behind today.
    default_end = date.today() - timedelta(days=7)
    parser = argparse.ArgumentParser(description="Daily weather ETL pipeline")
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=default_end - timedelta(days=6),
        help="YYYY-MM-DD",
    )
    parser.add_argument(
        "--end", type=date.fromisoformat, default=default_end, help="YYYY-MM-DD"
    )
    return parser.parse_args()


def run_pipeline(settings: Settings, start: date, end: date) -> int:
    """Run extract -> transform -> load for one date range."""
    extract_all(settings, start, end)  # API -> data/raw   (bronze)
    transform_all(settings, start, end)  # raw -> data/clean (silver)
    return load_all(settings, start, end)  # clean -> warehouse (gold)


def main():
    args = parse_args()
    settings = load_settings()
    setup_logging(settings.log_dir)

    if args.start > args.end:
        logger.error("--start (%s) must not be after --end (%s)", args.start, args.end)
        sys.exit(2)

    chunks = list(month_chunks(args.start, args.end))
    started = time.perf_counter()
    logger.info(
        "Pipeline started: %s to %s in %d monthly chunk(s)",
        args.start,
        args.end,
        len(chunks),
    )

    total_rows = 0
    for i, (chunk_start, chunk_end) in enumerate(chunks, start=1):
        logger.info("Chunk %d/%d: %s to %s", i, len(chunks), chunk_start, chunk_end)
        try:
            total_rows += run_pipeline(settings, chunk_start, chunk_end)
        except Exception:
            logger.exception(
                "Chunk %s to %s failed. Earlier chunks are saved; "
                "re-run from %s to continue.",
                chunk_start,
                chunk_end,
                chunk_start,
            )
            sys.exit(1)

    logger.info(
        "Pipeline finished: %d fact rows loaded in %.1f seconds",
        total_rows,
        time.perf_counter() - started,
    )


if __name__ == "__main__":
    main()

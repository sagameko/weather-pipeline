import argparse
import logging
import sys
import time
from datetime import date, timedelta

from weather_pipeline.config import load_settings
from weather_pipeline.extract.weather_api import extract_all
from weather_pipeline.load.warehouse import load_all
from weather_pipeline.logging_setup import setup_logging
from weather_pipeline.transform.clean_weather import transform_all

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


def main():
    args = parse_args()
    settings = load_settings()
    setup_logging(settings.log_dir)

    if args.start > args.end:
        logger.error("--start (%s) must not be after --end (%s)", args.start, args.end)
        sys.exit(2)

    started = time.perf_counter()
    logger.info("Pipeline started: %s to %s", args.start, args.end)
    try:
        extract_all(settings, args.start, args.end)  # API -> data/raw   (bronze)
        transform_all(settings, args.start, args.end)  # raw -> data/clean (silver)
        rows = load_all(settings, args.start, args.end)  # clean -> warehouse (gold)
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)

    logger.info(
        "Pipeline finished: %d fact rows loaded in %.1f seconds",
        rows,
        time.perf_counter() - started,
    )


if __name__ == "__main__":
    main()

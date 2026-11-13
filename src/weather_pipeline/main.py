import logging

from weather_pipeline.config import load_settings
from weather_pipeline.logging_setup import setup_logging

logger = logging.getLogger(__name__)

def main():
    settings = load_settings()
    setup_logging(settings.log_dir)

    logger.info("Pipeline started for %d locations", len(settings.locations))
    for loc in settings.locations:
        logger.debug("Location: %s, %s (%.2f, %.2f)",
                     loc.city, loc.state, loc.latitude, loc.longitude)


if __name__ == "__main__":
    main()
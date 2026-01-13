import logging
import sys
from datetime import datetime, timezone

from abs_sync.audiobookshelf.client import AudiobookshelfClient
from abs_sync.config import Config, LogFormat, LoggingConfig
from abs_sync.grist.client import GristClient
from abs_sync.sync import sync_audiobooks


def configure_logging(logging_config: LoggingConfig) -> None:
    format_strings = {
        LogFormat.FULL: "[{asctime}] [{levelname:<5s}] {message}",
        LogFormat.SYSTEMD: "[{levelname:<5s}] {message}",
        LogFormat.SIMPLE: "{message}",
    }

    logging.basicConfig(
        level=logging_config.level.value,
        format=format_strings[logging_config.format],
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        style="{",
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def main():
    try:
        config = Config()  # type: ignore[call-arg]
    except Exception as e:
        # Can't use logger yet as config failed
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Configure logging with settings from config
    configure_logging(config.logging)

    logger = logging.getLogger(__name__)

    finished_since = datetime(2026, 1, 4, 0, 0, 0, tzinfo=timezone.utc)  # TODO: Replace with real value

    with AudiobookshelfClient(config.abs) as abs_client:
        with GristClient(config.grist) as grist_client:
            try:
                logger.info("Starting synchronization...")
                sync_audiobooks(
                    abs_client=abs_client,
                    abs_user_id=config.abs.user_id,
                    grist_client=grist_client,
                    finished_since=finished_since,
                )
            except Exception as e:
                logger.error(f"Synchronization failed: {e}", exc_info=True)
                sys.exit(1)

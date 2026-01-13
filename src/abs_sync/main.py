import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from abs_sync.audiobookshelf.client import AudiobookshelfClient
from abs_sync.config import Config, LogFormat, LoggingConfig
from abs_sync.grist.client import GristClient
from abs_sync.state import StateData, load_state, save_state
from abs_sync.sync import sync_audiobooks

logger = logging.getLogger(__name__)

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize finished audiobooks from Audiobookshelf to Grist",
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=30),
    )
    parser.add_argument(
        "--since",
        "-s",
        type=str,
        help="Sync books finished since this timestamp (ISO 8601 format, e.g., 2026-01-01T00:00:00+00:00). "
        "If not provided, uses state file or default lookback period.",
        metavar="TIMESTAMP",
    )
    return parser.parse_args()


def determine_sync_start_time(
    cli_since: Optional[str],
    state_file_path: Path,
    default_lookback_minutes: int,
) -> datetime:
    """
    Determine the starting timestamp for synchronization.

    Priority order:
    1. CLI argument (--since)
    2. State file timestamp
    3. Current time - lookback_minutes
    """
    
    if cli_since:
        try:
            timestamp = datetime.fromisoformat(cli_since)
            logger.info(f"Using CLI-provided timestamp: {timestamp}")
            return timestamp
        except ValueError as e:
            logger.error(f"Invalid --since timestamp format: {e}")
            sys.exit(1)

    state = load_state(state_file_path)
    if state:
        logger.info(f"Using timestamp from state file: {state.last_sync_at}")
        return state.last_sync_at

    timestamp = datetime.now(timezone.utc) - timedelta(minutes=default_lookback_minutes)
    logger.info(f"No previous sync found, using default lookback: {timestamp} ({default_lookback_minutes} minutes)")
    return timestamp


def main():
    args = parse_args()

    try:
        config = Config()  # type: ignore[call-arg]
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    configure_logging(config.logging)

    finished_since = determine_sync_start_time(
        cli_since=args.since,
        state_file_path=config.state.file_path,
        default_lookback_minutes=config.default_lookback_minutes,
    )

    sync_start_time = datetime.now(timezone.utc)

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
                logger.info("Synchronization completed successfully")

                state = StateData(last_sync_at=sync_start_time)
                save_state(config.state.file_path, state)

            except Exception as e:
                logger.error(f"Synchronization failed: {e}", exc_info=True)
                sys.exit(1)

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StateData(BaseModel):
    last_sync_at: datetime


def load_state(state_file_path: Path) -> Optional[StateData]:
    if not state_file_path.exists():
        logger.debug(f"State file not found: {state_file_path}")
        return None

    try:
        state = StateData.model_validate_json(state_file_path.read_text())
        logger.info(f"Loaded state: last sync at {state.last_sync_at}")
        return state

    except Exception as e:
        logger.warning(f"Failed to parse state file: {e}")
        return None


def save_state(state_file_path: Path, state: StateData) -> None:
    try:
        state_file_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_file = state_file_path.with_suffix(".tmp")
        tmp_file.write_text(state.model_dump_json(indent=2))

        tmp_file.replace(state_file_path)
        logger.info(f"Saved state: last sync at {state.last_sync_at}")

    except Exception as e:
        logger.error(f"Failed to save state file: {e}", exc_info=True)
        raise

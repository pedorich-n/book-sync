import logging
from typing import Dict, Optional
from urllib.parse import urljoin

from requests import Session

from src.abs_sync.config import AbsConfig

from .models import AbsApiLibraryItem, AbsApiUser, AbsLibraryItemId, AbsUserId


class AudiobookshelfClient:
    """Client for interacting with the Audiobookshelf API."""

    def __init__(self, config: AbsConfig):
        self.logger = logging.getLogger(__name__)
        self.base_url = config.base_url
        self.session = Session()
        self.session.headers.update({"Authorization": f"Bearer {config.token.get_secret_value()}"})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        return False

    def _make_url(self, path: str) -> str:
        return urljoin(self.base_url.encoded_string(), f"/api/{path.lstrip('/')}")

    def _api_call(self, path: str, params: Dict[str, str] = {}, method: str = "GET") -> dict:
        url = self._make_url(path)
        response = self.session.request(method=method, url=url, params=params)
        response.raise_for_status()
        return response.json()

    def get_user(self, user_id: AbsUserId) -> Optional[AbsApiUser]:
        """
        Retrieve user information including media progress.

        Args:
            user_id: The user's ID

        Returns:
            User data if successful, None otherwise
        """
        try:
            data = self._api_call(f"users/{user_id}")
            return AbsApiUser.model_validate(data)
        except Exception as e:
            self.logger.error(f"Failed to get user {user_id}: {e}", exc_info=True)
            return None

    def get_library_item(self, library_item_id: AbsLibraryItemId) -> Optional[AbsApiLibraryItem]:
        """
        Retrieve detailed information about a library item.

        Args:
            library_item_id: The library item's ID

        Returns:
            Library item data if successful, None otherwise
        """
        try:
            data = self._api_call(f"items/{library_item_id}")
            return AbsApiLibraryItem.model_validate(data)
        except Exception as e:
            self.logger.error(f"Failed to get library item {library_item_id}: {e}", exc_info=True)
            return None

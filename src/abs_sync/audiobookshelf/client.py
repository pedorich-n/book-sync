import logging
from typing import Dict, Optional
from urllib.parse import urljoin

from pydantic import HttpUrl, SecretStr
from requests import Session

from .models import AbsApiLibraryItem, AbsApiUser, AbsLibraryItemId, AbsUserId


class AudiobookshelfClient:
    def __init__(self, token: SecretStr, base_url: HttpUrl):
        self.logger = logging.getLogger(__name__)
        self.token = token
        self.base_url = base_url
        self.session = Session()
        self.session.headers.update({"Authorization": f"Bearer {self.token.get_secret_value()}"})

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
        try:
            data = self._api_call(f"users/{user_id}")
            return AbsApiUser.model_validate(data)
        except Exception as e:
            self.logger.error(f"Failed to get current user: {e}", exc_info=True)
            return None

    def get_library_item(self, library_item_id: AbsLibraryItemId) -> Optional[AbsApiLibraryItem]:
        try:
            data = self._api_call(f"items/{library_item_id}")
            return AbsApiLibraryItem.model_validate(data)
        except Exception as e:
            self.logger.error(f"Failed to get library item {library_item_id}: {e}", exc_info=True)
            return None

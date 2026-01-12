import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from pygrister.api import GristApi  # type: ignore[import-untyped]

from src.abs_sync.config import GristConfig

from .models import (
    GristAuthorInput,
    GristAuthorRecord,
    GristBookInput,
    GristBookRecord,
    GristBookType,
    GristId,
    GristLanguageInput,
    GristLanguageRecord,
    GristReadInput,
    GristReadRecord,
    GristSeriesInput,
    GristSeriesRecord,
)


class GristClient:
    def __init__(self, config: GristConfig):
        self.logger = logging.getLogger(__name__)
        self.api = GristApi(config=config.get_pygrister_config())

        self.languages_table_id = "Languages"
        self.authors_table_id = "Authors"
        self.series_table_id = "Series"
        self.books_table_id = "Books"
        self.reads_table_id = "Reads"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.api.close_session()
        return False

    def get_or_create_language(self, name: str) -> Optional[GristId]:
        try:
            # Try to get existing language
            filter = {"Name": [name]}
            _, response = self.api.list_records(table_id=self.languages_table_id, filter=filter)
            decoded = [GristLanguageRecord.model_validate(record) for record in response]

            if decoded:
                id = decoded[0].id
                self.logger.debug(f"Found existing language: {name} (ID: {id})")
                return id

            # Create new language if not found
            input = GristLanguageInput(Name=name)
            _, response = self.api.add_records(
                table_id=self.languages_table_id,
                records=[input.model_dump()],
            )

            # Response from add_records should contain the new record IDs
            if response and len(response) > 0:
                ret = response[0]
                self.logger.debug(f"Created new language: {name} (ID: {ret})")
                return ret
            else:
                return None
        except Exception as e:
            self.logger.error(f"Failed to get or create language {name}: {e}")
            return None

    def get_or_create_author(
        self,
        name_primary: Optional[str] = None,
        name_local: Optional[str] = None,
        name_variants: Optional[str] = None,
    ) -> Optional[GristId]:
        try:
            # Try to get existing author
            filter = {}
            if name_primary:
                filter["Name_Primary"] = [name_primary]
            if name_local:
                filter["Name_Local"] = [name_local]

            _, response = self.api.list_records(table_id=self.authors_table_id, filter=filter)
            decoded = [GristAuthorRecord.model_validate(record) for record in response]

            if decoded:
                id = decoded[0].id
                self.logger.debug(f"Found existing author: {name_primary}, {name_local} (ID: {id})")
                return id

            # Create new author if not found
            input = GristAuthorInput(
                Name_Primary=name_primary,
                Name_Local=name_local,
                Name_Variants=name_variants,
            )
            _, response = self.api.add_records(
                table_id=self.authors_table_id,
                records=[input.model_dump()],
            )

            # Response from add_records should contain the new record IDs
            if response and len(response) > 0:
                ret = response[0]
                self.logger.debug(f"Created new author: {name_primary} (ID: {ret})")
                return ret
            else:
                return None
        except Exception as e:
            self.logger.error(f"Failed to get or create author {name_primary}: {e}")
            return None

    def get_or_create_series(self, name: str) -> Optional[GristId]:
        try:
            # Try to get existing series
            filter = {"Name": [name]}
            _, response = self.api.list_records(table_id=self.series_table_id, filter=filter)
            decoded = [GristSeriesRecord.model_validate(record) for record in response]

            if decoded:
                id = decoded[0].id
                self.logger.debug(f"Found existing series: {name} (ID: {id})")
                return id

            # Create new series if not found
            input = GristSeriesInput(Name=name)
            _, response = self.api.add_records(
                table_id=self.series_table_id,
                records=[input.model_dump()],
            )

            # Response from add_records should contain the new record IDs
            if response and len(response) > 0:
                ret = response[0]
                self.logger.debug(f"Created new series: {name} (ID: {ret})")
                return ret
            else:
                return None
        except Exception as e:
            self.logger.error(f"Failed to get or create series {name}: {e}")
            return None

    def get_or_create_book(
        self,
        title: str,
        authors: List[GristId],
        isbn: Optional[str] = None,
        asin: Optional[str] = None,
        title_original: Optional[str] = None,
        series: Optional[GristId] = None,
        series_order: Optional[int] = None,
        language_original: Optional[GristId] = None,
    ) -> Optional[GristId]:
        try:
            # Try to get existing book
            filter: Dict[str, Any] = {"Title": [title]}
            if authors:
                # Yes, double nested array is intentional.
                # Grist expects each filter entry to be a list of possible values, and Authors is a list itself, hence the nesting.
                filter["Authors"] = [authors]
            _, response = self.api.list_records(table_id=self.books_table_id, filter=filter)
            decoded = [GristBookRecord.model_validate(record) for record in response]

            if decoded:
                id = decoded[0].id
                self.logger.debug(f"Found existing book: {title} (ID: {id})")
                return id

            # Create new book if not found
            input = GristBookInput(
                Title=title,
                Language_Original=language_original,
                Authors=authors,
                ISBN=isbn,
                ASIN=asin,
                Title_Original=title_original,
                Series=series,
                Series_Order=series_order,
            )
            _, response = self.api.add_records(
                table_id=self.books_table_id,
                records=[input.model_dump()],
            )

            # Response from add_records should contain the new record IDs
            if response and len(response) > 0:
                ret = response[0]
                self.logger.debug(f"Created new book: {title} (ID: {ret})")
                return ret
            else:
                return None
        except Exception as e:
            self.logger.error(f"Failed to get or create book {title}: {e}")
            return None

    def get_or_create_read(
        self, book_id: GristId, date: date, book_type: GristBookType, language: Optional[GristId] = None
    ) -> Optional[GristId]:
        try:
            # Try to get existing read
            filter: Dict[str, Any] = {
                "Book": [book_id],
                "Date_Read": [datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc).timestamp()],
            }
            _, response = self.api.list_records(table_id=self.reads_table_id, filter=filter)
            decoded = [GristReadRecord.model_validate(record) for record in response]

            if decoded:
                id = decoded[0].id
                self.logger.debug(f"Found existing read for book ID {book_id} on date {date} (ID: {id})")
                return id

            # Create new read if not found
            input = GristReadInput(Book=book_id, Date_Read=date, Language_Read=language, Book_Type=book_type, Rating=None, Note=None)

            _, response = self.api.add_records(
                table_id=self.reads_table_id,
                records=[input.model_dump()],
            )

            # Response from add_records should contain the new record IDs
            if response and len(response) > 0:
                ret = response[0]
                self.logger.debug(f"Created new read for book ID {book_id} on date {date} (ID: {ret})")
                return ret
            else:
                return None
        except Exception as e:
            self.logger.error(f"Failed to get or create read for book ID {book_id} on date {date}: {e}")
            return None

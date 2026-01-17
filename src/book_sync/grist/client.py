import logging
from datetime import date
from typing import Any, Dict, List, Optional

from pygrister.api import GristApi

from book_sync.config import GristConfig
from book_sync.utils import NonEmptyStr, OptionalNonEmptyStr

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
    GristRecord,
    GristSeriesInput,
    GristSeriesRecord,
)
from .utils import date_to_grist_date


class GristClient:
    """Client for interacting with Grist tables to manage book reading records."""

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

    def _get_or_create_record[R: GristRecord](
        self,
        table_id: str,
        input_data: Dict[str, Any],
        filter_data: Dict[str, Any],
        record_type: type[R],
        entity_name: str,
    ) -> Optional[GristId]:
        """
        Generic helper to get an existing record or create a new one.

        Args:
            table_id: The Grist table identifier
            input_data: Data for creating a new record
            filter_data: Filter criteria to find existing records
            record_type: Pydantic model class for validating records (must have an 'id' attribute)
            entity_name: Human-readable name for logging

        Returns:
            The record ID if successful, None otherwise
        """
        try:
            # Try to get existing record
            _, records = self.api.list_records(table_id=table_id, filter=filter_data)
            decoded = [record_type.model_validate(record) for record in records]

            if decoded:
                record_id = decoded[0].id
                self.logger.debug(f"Found existing {entity_name} (ID: {record_id})")
                return record_id

            # Create new record if not found
            _, ids = self.api.add_records(table_id=table_id, records=[input_data])

            if ids and len(ids) > 0:
                record_id = ids[0]
                self.logger.debug(f"Created new {entity_name} (ID: {record_id})")
                return record_id
            else:
                self.logger.warning(f"Failed to create {entity_name}: empty response")
                return None
        except Exception as e:
            self.logger.error(f"Failed to get or create {entity_name}: {e}", exc_info=True)
            return None

    def get_or_create_language(self, name: str) -> Optional[GristId]:
        """
        Get an existing language record by name or create a new one.

        Args:
            name: The language name

        Returns:
            The language record ID if successful, None otherwise
        """
        input_data = GristLanguageInput(Name=name).model_dump()
        filter_data = {"Name": [name]}
        return self._get_or_create_record(
            table_id=self.languages_table_id,
            input_data=input_data,
            filter_data=filter_data,
            record_type=GristLanguageRecord,
            entity_name=f"language '{name}'",
        )

    def get_or_create_author(
        self,
        name_original: NonEmptyStr,
        name_reference: OptionalNonEmptyStr = None,
    ) -> Optional[GristId]:
        """
        Get an existing author record or create a new one.

        Args:
            name_original: The author's original name (in native script/language)
            name_reference: The author's reference name (in comfortable for reader script/language)

        Returns:
            The author record ID if successful, None otherwise
        """
        input_data = GristAuthorInput(
            Name_Original=name_original,
            Name_Reference=name_reference,
        ).model_dump()

        filter_data = {"Name_Original": [name_original]}
        if name_reference:
            filter_data["Name_Reference"] = [name_reference]

        return self._get_or_create_record(
            table_id=self.authors_table_id,
            input_data=input_data,
            filter_data=filter_data,
            record_type=GristAuthorRecord,
            entity_name=f"author '{name_original} {name_reference if name_reference else ''}'",
        )

    def get_or_create_series(
        self, name_original: NonEmptyStr, name_reference: OptionalNonEmptyStr = None
    ) -> Optional[GristId]:
        """
        Get an existing series record by name or create a new one.

        Args:
            name_original: The series original name (in native script/language)
            name_reference: The series reference name (in comfortable for reader script/language)

        Returns:
            The series record ID if successful, None otherwise
        """
        input_data = GristSeriesInput(Name_Original=name_original, Name_Reference=name_reference).model_dump()
        filter_data = {"Name_Original": [name_original]}
        if name_reference:
            filter_data["Name_Reference"] = [name_reference]

        return self._get_or_create_record(
            table_id=self.series_table_id,
            input_data=input_data,
            filter_data=filter_data,
            record_type=GristSeriesRecord,
            entity_name=f"series '{name_original} {name_reference if name_reference else ''}'",
        )

    def get_or_create_book(
        self,
        title_original: NonEmptyStr,
        authors: List[GristId],
        title_reference: OptionalNonEmptyStr = None,
        isbn: Optional[str] = None,
        asin: Optional[str] = None,
        series: Optional[GristId] = None,
        series_order: Optional[int] = None,
        language_original: Optional[GristId] = None,
    ) -> Optional[GristId]:
        """
        Get an existing book record or create a new one.

        Args:
            title_original: The book original title
            authors: List of author record IDs
            isbn: International Standard Book Number
            asin: Amazon Standard Identification Number
            title_reference: Reference title if translated
            series: Series record ID if book is part of a series
            series_order: Book's position in the series
            language_original: Original language record ID

        Returns:
            The book record ID if successful, None otherwise
        """
        input_data = GristBookInput(
            Title_Original=title_original,
            Title_Reference=title_reference,
            Language_Original=language_original,
            Authors=authors,
            ISBN=isbn,
            ASIN=asin,
            Series=series,
            Series_Order=series_order,
        ).model_dump()

        filter_data: Dict[str, Any] = {"Title_Original": [title_original]}
        if title_reference:
            filter_data["Title_Reference"] = [title_reference]
        if authors:
            # Double nested array is intentional: Grist expects each filter entry to be a list,
            # and Authors is already a list, hence the nesting.
            filter_data["Authors"] = [authors]

        return self._get_or_create_record(
            table_id=self.books_table_id,
            input_data=input_data,
            filter_data=filter_data,
            record_type=GristBookRecord,
            entity_name=f"book '{title_original} {title_reference if title_reference else ''}'",
        )

    def get_or_create_read(
        self,
        book_id: GristId,
        date: date,
        book_type: GristBookType,
        title_read: OptionalNonEmptyStr = None,
        language: Optional[GristId] = None,
    ) -> Optional[GristId]:
        """
        Get an existing read record or create a new one.

        Args:
            book_id: The book record ID
            date: Date when the book was finished
            book_type: Type of book (Audio, Digital, or Paper)
            title_read: Title as read (if different from original)
            language: Language record ID for the language read in

        Returns:
            The read record ID if successful, None otherwise
        """
        input_data = GristReadInput(
            Book=book_id,
            Title_Read=title_read,
            Date_Read=date,
            Language_Read=language,
            Book_Type=book_type,
            Rating=None,
            Note=None,
        ).model_dump()

        filter_data: Dict[str, Any] = {
            "Book": [book_id],
            "Date_Read": [date_to_grist_date(date)],
        }

        return self._get_or_create_record(
            table_id=self.reads_table_id,
            input_data=input_data,
            filter_data=filter_data,
            record_type=GristReadRecord,
            entity_name=f"read for book ID {book_id} {title_read if title_read else ''} on {date}",
        )

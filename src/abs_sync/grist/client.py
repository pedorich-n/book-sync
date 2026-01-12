import logging
from datetime import date
from typing import List, Optional

from pygrister.api import GristApi  # type: ignore[import-untyped]

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
    def __init__(self, api: GristApi):
        self.logger = logging.getLogger(__name__)
        self.api = api
        self.languages_table_id = "Languages"
        self.authors_table_id = "Authors"
        self.series_table_id = "Series"
        self.books_table_id = "Books"

    def get_language(self, name: str) -> Optional[GristLanguageRecord]:
        try:
            filter = {"Name": [name]}
            _, response = self.api.list_records(table_id=self.languages_table_id, filter=filter)
            decoded = [GristLanguageRecord.model_validate(record) for record in response]
            return decoded[0] if decoded else None
        except Exception as e:
            self.logger.error(f"Failed to get language by name {name}: {e}")
            return None

    def upsert_language(self, name: str) -> Optional[GristLanguageRecord]:
        try:
            input = GristLanguageInput(Name=name)
            upsert_record = input.to_upsert_record()
            self.api.add_update_records(
                table_id=self.languages_table_id,
                records=[upsert_record.model_dump()],
            )
            return self.get_language(name)
        except Exception as e:
            self.logger.error(f"Failed to upsert language {name}: {e}")
            return None

    def get_author(self, name_primary: Optional[str], name_local: Optional[str]) -> Optional[GristAuthorRecord]:
        try:
            filter = {}
            if name_primary:
                filter["Name_Primary"] = [name_primary]
            if name_local:
                filter["Name_Local"] = [name_local]

            _, response = self.api.list_records(table_id=self.authors_table_id, filter=filter)
            decoded = [GristAuthorRecord.model_validate(record) for record in response]
            return decoded[0] if decoded else None
        except Exception as e:
            self.logger.error(f"Failed to get author by primary name {name_primary}: {e}")
            return None

    def upsert_author(
        self,
        name_primary: str,
        name_local: Optional[str] = None,
        name_variants: Optional[str] = None,
    ) -> Optional[GristAuthorRecord]:
        try:
            input = GristAuthorInput(
                Name_Primary=name_primary,
                Name_Local=name_local,
                Name_Variants=name_variants,
            )
            upsert_record = input.to_upsert_record()
            self.api.add_update_records(
                table_id=self.authors_table_id,
                records=[upsert_record.model_dump()],
            )
            return self.get_author(name_primary=name_primary, name_local=name_local)
        except Exception as e:
            self.logger.error(f"Failed to upsert author {name_primary}: {e}")
            return None

    def get_series(self, name: str) -> Optional[GristSeriesRecord]:
        try:
            filter = {"Name": [name]}
            _, response = self.api.list_records(table_id=self.series_table_id, filter=filter)
            decoded = [GristSeriesRecord.model_validate(record) for record in response]
            return decoded[0] if decoded else None
        except Exception as e:
            self.logger.error(f"Failed to get series by name {name}: {e}")
            return None

    def upsert_series(self, name: str) -> Optional[GristSeriesRecord]:
        try:
            input = GristSeriesInput(Name=name)
            upsert_record = input.to_upsert_record()
            self.api.add_update_records(
                table_id=self.series_table_id,
                records=[upsert_record.model_dump()],
            )
            return self.get_series(name)
        except Exception as e:
            self.logger.error(f"Failed to upsert series {name}: {e}")
            return None

    def get_reads(self, book_id: GristId, date: Optional[date] = None) -> List[GristReadRecord]:
        try:
            filter = {"Book": [str(book_id)]}
            if date:
                filter["Date"] = [date.isoformat()]
            _, response = self.api.list_records(table_id="Reads", filter=filter)
            decoded = [GristReadRecord.model_validate(record) for record in response]
            return decoded
        except Exception as e:
            self.logger.error(f"Failed to get reads for book ID {book_id}: {e}")
            return []

    def upsert_read(
        self, book_id: GristId, date: date, book_type: GristBookType, language: Optional[GristId] = None
    ) -> Optional[GristReadRecord]:
        try:
            input = GristReadInput(Book=book_id, Date_Read=date, Language_Read=language, Type=book_type, Rating=None, Note=None)
            upsert_record = input.to_upsert_record()
            self.api.add_update_records(
                table_id="Reads",
                records=[upsert_record.model_dump()],
            )
            reads = self.get_reads(book_id, date)
            return reads[0] if reads else None
        except Exception as e:
            self.logger.error(f"Failed to upsert read for book ID {book_id} on date {date}: {e}")
            return None

    def get_book(self, title: str, authors: List[GristId]) -> Optional[GristBookRecord]:
        try:
            filter = {"Title": [title]}
            if authors:
                filter["Authors"] = [str(author) for author in authors]
            _, response = self.api.list_records(table_id=self.books_table_id, filter=filter)
            decoded = [GristBookRecord.model_validate(record) for record in response]
            return decoded[0] if decoded else None
        except Exception as e:
            self.logger.error(f"Failed to get book by title {title}: {e}")
            return None

    def upsert_book(
        self,
        title: str,
        authors: List[GristId],
        isbn: Optional[str] = None,
        asin: Optional[str] = None,
        title_original: Optional[str] = None,
        series: Optional[GristId] = None,
        series_order: Optional[int] = None,
        language_original: Optional[GristId] = None,
    ) -> Optional[GristBookRecord]:
        try:
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
            upsert_record = input.to_upsert_record()
            self.api.add_update_records(
                table_id=self.books_table_id,
                records=[upsert_record.model_dump()],
            )
            return self.get_book(title, authors)
        except Exception as e:
            self.logger.error(f"Failed to upsert book {title}: {e}")
            return None
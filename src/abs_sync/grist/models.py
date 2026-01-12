from datetime import date
from enum import Enum
from typing import Annotated, Any, List, NewType, Optional

from annotated_types import IsDigit
from pydantic import BaseModel, PositiveInt

from src.abs_sync.utils import NonEmptyList, NonEmptyStr, OptionalNonEmptyStr

GristId = NewType("GristId", int)
"""Type alias for Grist record IDs. To distinguish from other integers"""


class GristApiIdResponse(BaseModel):
    id: GristId


class GristApiResponse[X](BaseModel):
    records: List[X]


class GristUpsertRecord(BaseModel):
    """Base model for Grist upsert records with require/fields structure."""

    require: dict[str, Any]
    fields: dict[str, Any]


class GristLanguageBase(BaseModel):
    """Base model for Grist language records."""

    Name: NonEmptyStr


class GristLanguageInput(GristLanguageBase):
    def to_upsert_record(self) -> GristUpsertRecord:
        return GristUpsertRecord(
            require={"Name": self.Name},
            fields={},
        )


class GristLanguageRecord(GristLanguageBase):
    id: GristId


class GristAuthorBase(BaseModel):
    """Base model for Grist author records."""

    Name_Primary: NonEmptyStr
    Name_Local: OptionalNonEmptyStr
    Name_Variants: OptionalNonEmptyStr


class GristAuthorInput(GristAuthorBase):
    def to_upsert_record(self) -> GristUpsertRecord:
        return GristUpsertRecord(
            require={"Name_Primary": self.Name_Primary},
            fields={
                "Name_Local": self.Name_Local,
                "Name_Variants": self.Name_Variants,
            },
        )


class GristSeriesBase(BaseModel):
    """Base model for Grist series records."""

    Name: NonEmptyStr


class GristSeriesInput(GristSeriesBase):
    def to_upsert_record(self) -> GristUpsertRecord:
        return GristUpsertRecord(
            require={"Name": self.Name},
            fields={},
        )


class GristSeriesRecord(GristSeriesBase):
    id: GristId


class GristAuthorRecord(GristAuthorBase):
    id: GristId


class GristBookBase(BaseModel):
    """Base model for Grist book records."""

    Title: NonEmptyStr
    Title_Original: OptionalNonEmptyStr
    Authors: NonEmptyList[GristId]
    ISBN: OptionalNonEmptyStr
    ASIN: OptionalNonEmptyStr
    Language_Original: Optional[GristId]
    Series: Optional[GristId]
    Series_Order: Optional[PositiveInt]


class GristBookInput(GristBookBase):
    def to_upsert_record(self) -> GristUpsertRecord:
        return GristUpsertRecord(
            require={"Title": self.Title, "Authors": self.Authors},
            fields={
                "Title_Original": self.Title_Original,
                "ISBN": self.ISBN,
                "ASIN": self.ASIN,
                "Language_Original": self.Language_Original,
                "Series": self.Series,
                "Series_Order": self.Series_Order,
            },
        )


class GristBookRecord(GristBookBase):
    id: GristId


class GristBookType(str, Enum):
    AUDIO = "Audio"
    DIGITAL = "Digital"
    PAPER = "Paper"


class GristReadBase(BaseModel):
    """Base model for Grist read records."""

    Book: GristId
    Date_Read: date
    Language_Read: Optional[GristId]
    Rating: Optional[Annotated[str, IsDigit]]  # Rating is represented as a dropdown field in Grist
    Type: GristBookType
    Note: OptionalNonEmptyStr

class GristReadInput(GristReadBase):
    def to_upsert_record(self) -> GristUpsertRecord:
        return GristUpsertRecord(
            require={"Book": self.Book, "Date_Read": self.Date_Read},
            fields={
                "Language_Read": self.Language_Read,
                "Rating": self.Rating,
                "Type": self.Type,
                "Note": self.Note,
            },
        )

class GristReadRecord(GristReadBase):
    id: GristId
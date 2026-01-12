from datetime import date, datetime, time, timezone
from enum import Enum
from typing import Annotated, NewType, Optional

from annotated_types import IsDigit
from pydantic import BaseModel, PositiveInt, field_serializer, field_validator

from src.abs_sync.utils import NonEmptyList, NonEmptyStr, OptionalNonEmptyStr

GristId = NewType("GristId", int)
"""Type alias for Grist record IDs. To distinguish from other integers"""


class GristLanguageBase(BaseModel):
    """Base model for Grist language records."""

    Name: NonEmptyStr


class GristLanguageInput(GristLanguageBase):
    pass


class GristLanguageRecord(GristLanguageBase):
    id: GristId


class GristAuthorBase(BaseModel):
    """Base model for Grist author records."""

    Name_Primary: OptionalNonEmptyStr
    Name_Local: OptionalNonEmptyStr
    Name_Variants: OptionalNonEmptyStr


class GristAuthorInput(GristAuthorBase):
    pass


class GristSeriesBase(BaseModel):
    """Base model for Grist series records."""

    Name: NonEmptyStr


class GristSeriesInput(GristSeriesBase):
    pass


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
    @field_serializer("Authors")
    def serialize_Authors(self, authors: NonEmptyList[GristId]) -> NonEmptyList[str | GristId]:
        return ["L"] + [author for author in authors]


class GristBookRecord(GristBookBase):
    id: GristId

    @field_validator("Authors", mode="before")
    @classmethod
    def parse_grist_ids(cls, v):
        if isinstance(v, list) and len(v) > 0 and v[0] == "L":
            return v[1:] 
        return v


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
    Book_Type: GristBookType
    Note: OptionalNonEmptyStr


class GristReadInput(GristReadBase):

    @field_serializer("Date_Read")
    def serialize_Date_Read(self, value: date) -> int:
        return int(datetime.combine(value, time(), tzinfo=timezone.utc).timestamp())


class GristReadRecord(GristReadBase):
    id: GristId

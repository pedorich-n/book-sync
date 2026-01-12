from datetime import datetime
from enum import Enum
from typing import List, NewType, Optional

from pydantic import BaseModel, PositiveFloat

from src.abs_sync.utils import NonEmptyList, NonEmptyStr, OptionalNonEmptyStr

AbsLibraryItemId = NewType("AbsLibraryItemId", str)
AbsMediaId = NewType("AbsMediaId", str)
AbsUserId = NewType("AbsUserId", str)


class AbsApiMediaType(str, Enum):
    BOOK = "book"
    PODCAST = "podcast"


class AbsApiAuthor(BaseModel):
    name: NonEmptyStr


class AbsApiSeries(BaseModel):
    name: NonEmptyStr
    sequence: int


class AbsApiMediaItemMetadata(BaseModel):
    title: NonEmptyStr
    authors: NonEmptyList[AbsApiAuthor]
    series: List[AbsApiSeries]
    isbn: OptionalNonEmptyStr
    asin: OptionalNonEmptyStr
    language: OptionalNonEmptyStr


class AbsApiMediaItem(BaseModel):
    id: AbsMediaId
    metadata: AbsApiMediaItemMetadata


class AbsApiLibraryItem(BaseModel):
    id: AbsLibraryItemId
    media: AbsApiMediaItem


class AbsApiMediaProgress(BaseModel):
    id: AbsMediaId
    userId: AbsUserId
    libraryItemId: AbsLibraryItemId
    mediaItemType: AbsApiMediaType
    progress: PositiveFloat
    isFinished: bool
    finishedAt: Optional[datetime]
    displayTitle: NonEmptyStr


class AbsApiUser(BaseModel):
    id: AbsUserId
    username: NonEmptyStr
    mediaProgress: List[AbsApiMediaProgress]

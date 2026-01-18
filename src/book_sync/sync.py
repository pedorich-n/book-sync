import logging
from datetime import datetime
from typing import List, Optional

from book_sync.audiobookshelf import AbsApiMediaProgress, AbsUserId, AudiobookshelfClient
from book_sync.grist import GristBookType, GristClient, GristId

logger = logging.getLogger(__name__)


class SyncError(Exception):
    pass


def sync_audiobooks(
    abs_client: AudiobookshelfClient,
    abs_user_id: AbsUserId,
    grist_client: GristClient,
    finished_since: datetime,
) -> None:
    """
    Synchronize finished audiobooks from Audiobookshelf to Grist.
    """
    logger.info(f"Starting sync for user {abs_user_id} from {finished_since}")

    # Step 1: Get user's media progress
    user = abs_client.get_user(abs_user_id)
    if not user:
        raise SyncError(f"Failed to get user {abs_user_id}")

    # Step 2: Filter for finished items after the specified datetime
    finished_items = [
        progress
        for progress in user.mediaProgress
        if progress.isFinished and progress.finishedAt and progress.finishedAt > finished_since
    ]

    logger.info(f"Found {len(finished_items)} finished items to sync")

    # Step 3: Process each finished item
    for progress in finished_items:
        _sync_single_item(abs_client, grist_client, progress)

    logger.info("Sync completed")


def _sync_single_item(
    abs_client: AudiobookshelfClient,
    grist_client: GristClient,
    progress: AbsApiMediaProgress,
) -> None:
    """
    Sync a single library item from ABS to Grist.
    """
    logger.info(f"Syncing: {progress.displayTitle} (finished at {progress.finishedAt})")

    library_item = abs_client.get_library_item(progress.libraryItemId)
    if not library_item:
        raise SyncError(f"Failed to get library item {progress.libraryItemId}")

    metadata = library_item.media.metadata

    # Step 1: Upsert language
    language_id: Optional[GristId] = None
    if metadata.language:
        language_id = grist_client.get_or_create_language(name=metadata.language)

    if language_id:
        logger.info(f"Upserted language: {metadata.language} (ID: {language_id})")
    else:
        raise SyncError(f"Failed to upsert language: {metadata.language}")

    # Step 2: Upsert authors
    author_ids: List[GristId] = []
    for abs_author in metadata.authors:
        author_name = abs_author.name

        # We're going to assume that author's name is in the original language
        author_id = grist_client.get_or_create_author(name_original=author_name)

        if author_id:
            author_ids.append(author_id)
            logger.info(f"Upserted author: {author_name} (ID: {author_id})")
        else:
            raise SyncError(f"Failed to upsert author: {author_name}")

    if not author_ids:
        raise SyncError(f"No authors available for book: {metadata.title}")

    # Step 3: Upsert series
    series_id: Optional[GristId] = None
    series_order: Optional[int] = None
    if metadata.series:
        first_series = metadata.series[0]
        series_order = first_series.sequence

        # We're going to assume that series name is in the original language
        series_id = grist_client.get_or_create_series(name_original=first_series.name)

        if series_id:
            logger.info(f"Upserted series: {first_series.name} (ID: {series_id})")
        else:
            raise SyncError(f"Failed to upsert series: {first_series.name}")

    # Step 4: Upsert book
    # We're going to assume that book title is in the original language
    book_id = grist_client.get_or_create_book(
        title_original=metadata.title,
        authors=author_ids,
        isbn=metadata.isbn,
        asin=metadata.asin,
        title_reference=None,  # No way to know for sure, so leaving empty
        series=series_id,
        series_order=series_order,
        language_original=None,  # No way to know for sure, so leaving empty
    )

    if book_id:
        logger.info(f"Upserted book: {metadata.title} (ID: {book_id})")
    else:
        raise SyncError(f"Failed to upsert book: {metadata.title}")

    # Step 5: Upsert read record
    read_date = progress.finishedAt.date()  # type: ignore[union-attr] # If we're here, finishedAt shouldn't be None
    # We're going to assume that read title is the same as the original title
    read_id = grist_client.get_or_create_read(
        book_id=book_id,
        date=read_date,
        book_type=GristBookType.AUDIO,
        title_read=None,  # No way to know for sure, so leaving empty
        language=language_id,
    )

    if read_id:
        logger.info(f"Upserted read: Book '{metadata.title}' on {read_date} (ID: {read_id})")
    else:
        raise SyncError(f"Failed to upsert read for book: {metadata.title}")

import logging
from datetime import datetime
from typing import List, Optional

from src.abs_sync.audiobookshelf import AbsApiMediaProgress, AbsUserId, AudiobookshelfClient
from src.abs_sync.grist import GristBookType, GristClient, GristId
from src.abs_sync.utils import is_latin_alphabet

logger = logging.getLogger(__name__)


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
        logger.error(f"Failed to get user {abs_user_id}")
        return

    # Step 2: Filter for finished items after the specified datetime
    finished_items = [
        progress for progress in user.mediaProgress if progress.isFinished and progress.finishedAt and progress.finishedAt > finished_since
    ]

    logger.info(f"Found {len(finished_items)} finished items to sync")

    # Step 3: Process each finished item
    for progress in finished_items:
        try:
            _sync_single_item(abs_client, grist_client, progress)
        except Exception as e:
            logger.error(f"Failed to sync item {progress.libraryItemId} ({progress.displayTitle}): {e}", exc_info=True)
            continue

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
        logger.error(f"Failed to get library item {progress.libraryItemId}")
        return

    metadata = library_item.media.metadata

    # Step 1: Upsert language
    language_id: Optional[GristId] = None
    if metadata.language:
        language_id = grist_client.get_or_create_language(name=metadata.language)

    if language_id:
        logger.info(f"Upserted language: {metadata.language} (ID: {language_id})")
    else:
        logger.warning(f"Failed to upsert language: {metadata.language}")

    # Step 2: Upsert authors
    author_ids: List[GristId] = []
    for abs_author in metadata.authors:
        author_name = abs_author.name
        is_latin = is_latin_alphabet(author_name)
        primary_name = None
        local_name = None

        if is_latin:
            primary_name = author_name
        else:
            local_name = author_name

        author_id = grist_client.get_or_create_author(name_primary=primary_name, name_local=local_name, name_variants=None)

        if author_id:
            author_ids.append(author_id)
            logger.info(f"Upserted author: {author_name} (ID: {author_id})")
        else:
            logger.warning(f"Failed to upsert author: {author_name}")

    if not author_ids:
        logger.error(f"No authors available for book: {metadata.title}")
        return

    # Step 3: Upsert series
    series_id: Optional[GristId] = None
    series_order: Optional[int] = None
    if metadata.series:
        first_series = metadata.series[0]
        series_order = first_series.sequence
        series_id = grist_client.get_or_create_series(name=first_series.name)

        if series_id:
            logger.info(f"Upserted series: {first_series.name} (ID: {series_id})")
        else:
            logger.warning(f"Failed to upsert series: {first_series.name}")

    # Step 4: Upsert book
    book_id = grist_client.get_or_create_book(
        title=metadata.title,
        authors=author_ids,
        isbn=metadata.isbn,
        asin=metadata.asin,
        title_original=None,  # No way to know for sure, so leaving empty
        series=series_id,
        series_order=series_order,
        language_original=None,  # No way to know for sure, so leaving empty
    )

    if book_id:
        logger.info(f"Upserted book: {metadata.title} (ID: {book_id})")
    else:
        logger.warning(f"Failed to upsert book: {metadata.title}")
        return

    # Step 5: Upsert read record
    read_date = progress.finishedAt.date()  # type: ignore[union-attr] # If we're here, finishedAt shouldn't be None
    read_id = grist_client.get_or_create_read(
        book_id=book_id,
        date=read_date,
        book_type=GristBookType.AUDIO,
        language=language_id,
    )

    if read_id:
        logger.info(f"Upserted read: Book '{metadata.title}' on {read_date} (ID: {read_id})")
    else:
        logger.warning(f"Failed to upsert read for book: {metadata.title}")

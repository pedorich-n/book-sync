from typing import Annotated, Any, List, Optional

from annotated_types import MinLen
from pydantic import BeforeValidator


def _empty_str_to_none(v: Any) -> Optional[str]:
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


type OptionalNonEmptyStr = Annotated[Optional[str], BeforeValidator(_empty_str_to_none)]

type NonEmptyStr = Annotated[str, MinLen(1)]

type NonEmptyList[T] = Annotated[List[T], MinLen(1)]


def is_latin_alphabet(text: NonEmptyStr) -> bool:
    """
    Check if text contains at least one Latin alphabet character.

    Args:
        text: The text to check

    Returns:
        True if at least one Latin alphabet character is present, False otherwise
    """
    return any(c.isalpha() and c.isascii() for c in text)

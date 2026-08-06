from typing import Annotated, Any

from annotated_types import MinLen
from pydantic import BeforeValidator


def _empty_str_to_none(v: Any) -> str | None:
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


type OptionalNonEmptyStr = Annotated[str | None, BeforeValidator(_empty_str_to_none)]

type NonEmptyStr = Annotated[str, MinLen(1)]

type NonEmptyList[T] = Annotated[list[T], MinLen(1)]


def construct_log_values(**kwargs: Any) -> str:
    return ", ".join(f"{key}={value}" for key, value in kwargs.items() if value)

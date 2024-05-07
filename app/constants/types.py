from enum import StrEnum
from typing import TypedDict

__all__ = (
    "CONTACT",
    "Keys",
)


class Keys(StrEnum):
    LANGUAGE: str = "language"
    ADD_AUTHOR_MENTION: str = "add_author_mention"
    ADD_ORIGINAL_LINK: str = "add_original_link"
    TIKTOK_FLAG: str = "tiktok_flag"
    DESCRIPTION_FLAG: str = "description_flag"
    ADD_DESCRIPTION: str = "add_description"
    HISTORY: str = "history"
    ADD_MEDIA_SOURCE: str = "add_media_source"


class CONTACT(TypedDict):
    type: str
    text: str
    url: str

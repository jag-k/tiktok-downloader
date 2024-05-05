from enum import StrEnum
from typing import TypedDict


class Keys(StrEnum):
    LANGUAGE = "language"
    ADD_AUTHOR_MENTION = "add_author_mention"
    ADD_ORIGINAL_LINK = "add_original_link"
    TIKTOK_FLAG = "tiktok_flag"
    DESCRIPTION_FLAG = "description_flag"
    ADD_DESCRIPTION = "add_description"
    HISTORY = "history"
    ADD_MEDIA_SOURCE = "add_media_source"


class CONTACT(TypedDict):
    type: str
    text: str
    url: str

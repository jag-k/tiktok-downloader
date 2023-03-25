from enum import Enum
from typing import TypedDict


class Keys(str, Enum):
    LANGUAGE = "language"
    ADD_AUTHOR_MENTION = "add_author_mention"
    ADD_ORIGINAL_LINK = "add_original_link"
    TIKTOK_FLAG = "tiktok_flag"
    DESCRIPTION_FLAG = "description_flag"
    HISTORY = "history"
    ADD_MEDIA_SOURCE = "add_media_source"


class CONTACT(TypedDict):
    type: str
    text: str
    url: str

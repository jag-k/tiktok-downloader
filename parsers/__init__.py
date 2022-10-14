from parsers.base import Parser, Video
from parsers.tiktok import Parser as _  # noqa
from parsers.tweeter import Parser as _  # noqa
from parsers.youtube import Parser as _  # noqa

__all__ = (
    "Parser",
    "Video",
)

from enum import Enum

from app.models.base import Model


class ReportType(str, Enum):
    BUG = "bug"
    WRONG_MEDIA: str = "wrong_media"
    MEDIA_NOT_FOUND: str = "media_not_found"
    OTHER: str = "other"


class ReportPlace(str, Enum):
    CODE = "code"
    INLINE = "inline"
    MESSAGE = "message"
    OTHER = "other"


class Report(Model):
    report_type: ReportType
    message: str
    report_place: ReportPlace = ReportPlace.OTHER
    extra_data: dict | None = None

    def __str__(self):
        return self.message

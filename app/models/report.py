from enum import StrEnum

from .base import Model

__all__ = (
    "Report",
    "ReportType",
    "ReportPlace",
)


class ReportType(StrEnum):
    BUG = "bug"
    WRONG_MEDIA: str = "wrong_media"
    MEDIA_NOT_FOUND: str = "media_not_found"
    OTHER: str = "other"


class ReportPlace(StrEnum):
    CODE = "code"
    INLINE = "inline"
    MESSAGE = "message"
    OTHER = "other"


class Report(Model):
    report_type: ReportType
    message: str
    report_place: ReportPlace = ReportPlace.OTHER
    extra_data: dict | None = None

    def __str__(self) -> str:
        return self.message

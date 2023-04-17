import json
from datetime import datetime
from os import PathLike
from pathlib import Path

import aiofiles
from telegram import Update

from app.constants import REPORT_PATH
from app.context import CallbackContext
from app.models.report import Report
from app.utils.notify.base import MessageType, Notify


class FileReporter(Notify):
    """
    Reporter that writes reports to a file.

    :param file_path: Path to report file
    :default file_path: $REPORT_PATH
    """

    SUPPORTED_TYPES = {MessageType.REPORT}

    def __init__(
        self,
        *,
        file_path: PathLike = REPORT_PATH,
        types: set[MessageType] = None
    ):
        super().__init__(types=types)
        p = Path(file_path)
        if not p.exists():
            with p.open("w") as f:
                f.write("[]")
        self.path = file_path

    @property
    def _is_active(self) -> bool:
        return True

    async def _send_message(
        self,
        message_type: MessageType,
        text: str,
        update: Update | None = None,
        ctx: CallbackContext | None = None,
        extras: dict | None = None,
    ) -> bool:
        report: Report | None = extras.get("report", None)
        if not report:
            return False

        date = datetime.now()
        if (
            update
            and update.effective_message
            and update.effective_message.date
        ):
            date = update.effective_message.date

        async with aiofiles.open(self.path, "r") as f:
            report_old = await f.read()
        reports = json.loads(report_old)
        report_data = report.to_dict()
        report_data.pop("@type", None)

        reports.append(
            {
                "date": date.isoformat(),
                **self._user_data_from_update(update),
                **report_data,
            }
        )

        resp = json.dumps(reports, indent=4, ensure_ascii=False)
        async with aiofiles.open(self.path, "w") as f:
            await f.write(resp)
        return True

import json
from datetime import datetime
from os import PathLike
from pathlib import Path

import aiofiles
from telegram import Update

from app.constants import REPORT_PATH
from app.context import CallbackContext
from app.utils.notify.base import MessageType, Notify


class FileReporter(Notify):
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
            raise FileNotFoundError(p)
        self.path = file_path

    @property
    def _is_active(self) -> bool:
        return True

    async def _send_message(
        self,
        message_type: MessageType,
        text: str,
        update: Update,
        extras: dict,
        ctx: CallbackContext = None,
    ) -> bool:
        report_args = extras.get("report_args", [])
        if not report_args:
            return False

        date = datetime.now()
        if update.effective_message and update.effective_message.date:
            date = update.effective_message.date

        async with aiofiles.open(self.path, "r") as f:
            report_old = await f.read()
        report = json.loads(report_old)

        for i in report_args:
            report.append(
                {
                    "report": i,
                    "date": date.isoformat(),
                    **self._user_data_from_update(update),
                }
            )

        resp = json.dumps(report, indent=4, ensure_ascii=False)
        async with aiofiles.open(self.path, "w") as f:
            await f.write(resp)
        return True

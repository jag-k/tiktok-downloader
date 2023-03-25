import json
from datetime import datetime

import aiofiles as aiofiles
from telegram import Update

from app.constants import REPORT_PATH


def _load_report() -> list[dict]:
    if REPORT_PATH.exists():
        with open(REPORT_PATH) as f:
            return json.load(f)
    return []


def _make_report_dict(update: Update, report_str: str) -> dict:
    date = datetime.now()
    if update.effective_message:
        date = update.effective_message.date
    user = update.effective_user
    return {
        "report": report_str,
        "user": user.id if user else None,
        "username": user.username if user.username else None,
        "user_link": user.link if user else None,
        "date": date.isoformat(),
    }


def add_report(update: Update, report_args: list[str]) -> None:
    report = _load_report()

    if report_args:
        for i in report_args:
            report.append(_make_report_dict(update, i))

    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)


async def async_add_report(update: Update, report_args: list[str]) -> None:
    report = _load_report()

    if report_args:
        for i in report_args:
            report.append(_make_report_dict(update, i))

    resp = json.dumps(report, indent=4, ensure_ascii=False)
    async with aiofiles.open(REPORT_PATH, "w") as f:
        await f.write(resp)

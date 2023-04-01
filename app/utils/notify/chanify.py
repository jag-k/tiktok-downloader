import io
import logging
import mimetypes
import traceback
from datetime import datetime
from enum import Enum
from typing import TypedDict

import httpx
from telegram import Update, User

from app.constants import CONTEXT_VARS
from app.context import CallbackContext
from app.utils.minmax import minmax
from app.utils.notify.base import MessageType, Notify

logger = logging.getLogger(__name__)

__all__ = ("Chanify", "InterruptionLevel")


class Action(TypedDict):
    name: str
    url: str


def clear(d: dict) -> dict | None:
    return {k: v for k, v in d.items() if v} or None


class InterruptionLevel(str, Enum):
    # Lights up screen and may play a sound.
    active = "active"
    # Does not light up screen or play sound.
    passive = "passive"
    # Lights up screen and may play a sound;
    # May be presented during Do Not Disturb.
    time_sensitive = "time-sensitive"


class ChanifyApi:
    def __init__(self, url: str, token: str):
        self._url = url
        self._token = token

    @property
    def url(self):
        return f"{self._url}/v1/sender/{self._token}"

    async def __aenter__(self):
        # self._session = getattr(self, '_session', None)
        self._session: httpx.AsyncClient | None = getattr(
            self, "_session", None
        )
        self._session_enter: httpx.AsyncClient | None = getattr(
            self, "_session_enter", None
        )
        self._session_counter: int = getattr(self, "_session_counter", 0)
        if not self._session or not self._session_enter:
            self._session = httpx.AsyncClient()
            self._session_enter = await self._session.__aenter__()
        self._session_counter += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._session_counter -= 1
        if self._session_counter <= 0:
            self._session_enter = None
            s = self._session
            self._session = None
            return await s.__aexit__(exc_type, exc_val, exc_tb)

    async def send_text(
        self,
        title: str = None,
        text: str = None,
        copy: str = None,
        auto_copy: bool = False,
        sound: bool | str = False,
        priority: int = 10,
        interruption_level: InterruptionLevel = InterruptionLevel.active,
        actions: list[Action] = None,
    ) -> httpx.Response:
        if not actions:
            actions = []
        d = {
            "title": title,
            "text": text,
            "copy": copy,
            "autocopy": int(auto_copy),
            "sound": sound if isinstance(sound, str) else int(sound),
            "priority": minmax(5, priority, 10),
            "interruption-level": interruption_level.value,
            "actions": [f"{a['name']}|{a['url']}" for a in actions[:4]],
        }
        async with self:
            return await self._session_enter.post(self.url, json=clear(d))

    async def send_link(
        self,
        link: str,
        sound: bool | str = False,
        priority: int = 10,
        **kwargs,
    ) -> httpx.Response:
        d = {
            "link": link,
            "sound": sound if isinstance(sound, str) else int(sound),
            "priority": minmax(5, priority, 10),
            **kwargs,
        }
        async with self:
            return await self._session_enter.post(self.url, json=clear(d))

    async def _send_file(
        self,
        file: bytes | io.FileIO,
        text: str = None,
        file_name: str = "file.txt",
        **kwargs,
    ) -> httpx.Response:
        data = {**kwargs}
        mime_type, _ = mimetypes.guess_type(file_name)
        if file_name:
            data["filename"] = file_name
        if text:
            data["text"] = text

        async with self:
            res = await self._session_enter.post(
                self.url,
                data=data,
                files={
                    "file": (file_name, file, mime_type),
                },
            )
            if res.status_code == 400:
                logger.warning("Chanify not support file upload!")

            return res

    async def send_file(
        self,
        file: bytes | io.FileIO,
        text: str = None,
        file_name: str = "file.txt",
        **kwargs,
    ) -> httpx.Response:
        return await self._send_file(file, text, file_name, **kwargs)

    async def send_image(
        self,
        image: bytes,
        text: str | None = None,
        **kwargs,
    ) -> httpx.Response:
        return await self._send_file(image, text, "image.jpg", **kwargs)

    async def send_audio(
        self,
        audio: bytes | io.FileIO,
        text: str | None = None,
        file_name: str | None = "audio.mp3",
        **kwargs,
    ) -> httpx.Response:
        return await self._send_file(audio, text, file_name, **kwargs)


class Chanify(Notify):
    SUPPORTED_TYPES = {MessageType.REPORT, MessageType.EXCEPTION}

    def __init__(
        self,
        *,
        token: str,
        url: str = "https://api.chanify.net",
        types: set[MessageType] = None,
    ):
        super().__init__(types=types)
        self.client = ChanifyApi(url, token)

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
        try:
            match message_type:
                case MessageType.REPORT:
                    report_args = extras.get("report_args", [])
                    if not report_args:
                        return False
                    date = None
                    if update.effective_message:
                        date = update.effective_message.date
                    res = await self._send_message_report(
                        user=update.effective_user,
                        date=date,
                        reports=report_args,
                    )
                case MessageType.EXCEPTION:
                    if not ctx.error:
                        return False
                    res = await self._send_message_exception(
                        user=update.effective_user, exc=ctx.error
                    )
                case _:
                    res = await self.client.send_text(text=text)
            res.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed to send Chanify message: %s: %s",
                exc.response.status_code,
                exc.response.json(),
                exc_info=exc,
            )
        except Exception as exc:
            logger.error("Failed to send Chanify message", exc_info=exc)
        return False

    async def _send_message_report(
        self,
        reports: list[str],
        user: User | None,
        date: datetime = None,
    ) -> httpx.Response:
        if not date:
            date = datetime.now()

        title = f"Found {len(reports)} report(s)"
        actions: list[Action] = [
            Action(name=f"Open {i} link", url=r)
            for i, r in enumerate(reports, 1)
        ]
        copy: str = "\n".join(reports)

        if user:
            title += f" from {user.name}"
            copy += f"\n\nUser Link: {user.link}"
            actions.append(
                Action(
                    name=f"Open {user.name}'s chat",
                    url=user.link,
                )
            )

        return await self.client.send_text(
            title=f"{title}!",
            text="\n".join(reports)
            + f"\n\nat {date.isoformat(' ', 'seconds')}",
            copy=copy,
            sound=True,
            actions=actions,
        )

    async def _send_message_exception(
        self,
        user: User | None,
        exc: Exception,
    ) -> httpx.Response:
        title = f"Exception {exc}"

        actions: list[Action] = []
        text = "".join(traceback.format_exception(exc))
        user_copy = ""
        if user:
            title += f" from {user.name}"
            user_copy = f"User Link: {user.link}"
            actions.append(
                Action(
                    name=f"Open {user.name}'s chat",
                    url=user.link,
                )
            )
        context_vars = "\n".join(
            f"{var.name}: {var.get()}" for var in CONTEXT_VARS
        )
        res = await self.client.send_text(
            title=f"{title}!",
            text=(
                f"Traceback in next message file.\n"
                f"Context Vars:\n"
                f"{context_vars}\n\n"
                f"{user_copy}"
            ),
            copy=user_copy,
            sound=True,
            actions=actions,
        )
        res.raise_for_status()

        return await self.client.send_file(
            text.encode("utf-8"),
            "Traceback",
            "traceback.txt",
        )

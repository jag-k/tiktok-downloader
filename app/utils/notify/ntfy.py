import logging
import traceback
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Self

import httpx
from telegram import Update, User

from app.constants import CONTEXT_VARS
from app.context import CallbackContext
from app.models.report import Report
from app.utils.notify.base import MessageType, Notify

logger = logging.getLogger(__name__)

__all__ = ("Ntfy", "InterruptionLevel")


@dataclass
class FileAttachment:
    content: str | bytes
    filename: str

    @property
    def headers(self) -> dict[str, str]:
        return {
            "X-Filename": self.filename,
        }

    @property
    def method(self) -> Literal["POST", "PUT"]:
        return "PUT"

    @property
    def files(self) -> bytes:
        if isinstance(self.content, str):
            return self.content.encode("utf-8")

        return self.content

    def __bool__(self):
        return bool(self.content)


@dataclass
class Action(ABC):
    label: str

    @classmethod
    def from_list(cls, actions: list[Self]) -> str:
        return "; ".join(map(str, actions))

    @abstractmethod
    def __str__(self):
        raise NotImplementedError


class ActionBroadcast(Action):
    extras: dict[str, str]
    intent: str = "io.heckel.ntfy.USER_ACTION"
    clear: bool = False

    def __str__(self):
        a = ["broadcast", self.label]
        if self.extras:
            a.extend(f"extras.{k}={v}" for k, v in self.extras.items())
        if self.intent:
            a.append(f"intent={self.intent}")
        if self.clear:
            a.append("clear=true")
        return ", ".join(a)


@dataclass
class ActionView(Action):
    url: str
    clear: bool = False

    def __str__(self):
        a = ["view", self.label, self.url]
        if self.clear:
            a.append("clear=true")
        return ", ".join(a)


class ActionHttp(Action):
    url: str
    method: Literal["GET", "POST", "PUT", "DELETE"] = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    clear: bool = False

    def __str__(self):
        a = ["http", self.label, self.url]
        if self.method:
            a.append(f"method={self.method}")
        if self.headers:
            a.extend(f"headers.{k}={v}" for k, v in self.headers.items())
        if self.body:
            a.append(f"body={self.body}")
        if self.clear:
            a.append("clear=true")
        return ", ".join(a)


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


class NtfyApi:
    def __init__(
        self,
        url: str = "https://ntfy.sh",
        topic: str = "topic",
        token: str = None,
        token_type: str = "Bearer",
    ):
        self._url = url
        self._token = token
        self._topic = topic
        self._token_type = token_type

    @property
    def url(self):
        return f"{self._url}/{self._topic}"

    async def __aenter__(self):
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

    async def send(
        self,
        message: str = None,
        title: str = None,
        priority: Literal[1, 2, 3, 4, 5] = None,
        tags: list[str] = None,
        delay: str = None,
        actions: list[Action] = None,
        click: str = None,
        icon: str = None,
        file: FileAttachment = None,
        **kwargs,
    ) -> httpx.Response:

        method_type = file.method if file else "POST"
        data = file.files if file else None
        print(type(message))
        print(message)

        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"{self._token_type} {self._token}"
        if title:
            headers["X-Title"] = title
        if priority:
            headers["X-Priority"] = str(priority)
        if tags:
            headers["X-Tags"] = ",".join(tags)
        if delay:
            headers["X-Delay"] = delay
        if actions:
            headers["X-Actions"] = Action.from_list(actions)
        if click:
            headers["X-Click"] = click
        if file:
            headers |= file.headers
        if icon:
            headers["X-Icon"] = icon
        if kwargs:
            headers |= {
                f"X-{k.replace('_', '-').title()}": str(v)
                for k, v in kwargs.items()
            }
        if message:
            if not data:
                data = message
            else:
                headers["X-Message"] = message
        print(headers)
        headers = {
            k: v.decode("utf-8") if isinstance(v, bytes) else str(v)
            for k, v in headers.items()
        }
        async with self:
            return await self._session_enter.request(
                method_type, self.url, data=data, headers=headers
            )


class Ntfy(Notify):
    """
    A wrapper for [Ntfy](https://ntfy.sh) Notifications

    :param url: Ntfy server url
    :default url: https://ntfy.sh
    :param topic: Ntfy topic
    :default topic: video-downloader
    :param token: Ntfy token
    :default token: None
    :param token_type: Ntfy token type (Bearer or Basic)
    :default token_type: Bearer
    :param send_file: Send file with notification
    :default send_file: False
    """

    SUPPORTED_TYPES = set(MessageType)

    def __init__(
        self,
        *,
        url: str = "https://ntfy.sh",
        topic: str = "video-downloader",
        token: str = None,
        token_type: str = "Bearer",
        send_file: bool = False,
        types: set[MessageType] = None,
    ):
        super().__init__(types=types)
        self.client = NtfyApi(url, topic, token, token_type)
        self.send_file = send_file

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
        func: Coroutine[Any, Any, httpx.Response]

        match message_type:
            case MessageType.REPORT:
                report: Report = extras.get("report", None)
                if not report:
                    return False
                date = None
                if update and update.effective_message:
                    date = update.effective_message.date
                func = self._send_message_report(
                    user=update.effective_user,
                    date=date,
                    report=report,
                )
            case MessageType.EXCEPTION:
                if not ctx.error:
                    return False
                func = self._send_message_exception(
                    user=getattr(update, "effective_user", None),
                    exc=ctx.error,
                )
            case _:
                func = self.client.send(
                    title=text,
                    message=f"Message type: {message_type.value}",
                    tags=[message_type.value],
                    priority=2,
                )

        try:
            res = await func
            res.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed to send Ntfy message: %s: %s",
                exc.response.status_code,
                exc.response.json(),
                exc_info=exc,
            )
        return False

    async def _send_message_report(
        self,
        report: Report,
        user: User | None,
        date: datetime = None,
    ) -> httpx.Response:
        if not date:
            date = datetime.now()

        title = "Found report"
        actions: list[Action] = [
            ActionView(label="Open link", url=report.message),
        ]

        if user:
            title += f" from {user.name}"
            actions.append(
                ActionView(
                    label=f"Open {user.name}'s chat",
                    url=user.link,
                )
            )

        return await self.client.send(
            title=f"{title}!",
            message=(
                f"Message: {report.message!r}\n"
                f"Report place: {report.report_place.value!r}\n"
                f"Report Type: {report.report_type.value!r}\n\n"
                f"at {date.isoformat(' ', 'seconds')}"
            ),
            priority=4,
            tags=["report"],
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
            user_copy = f"\n\nUser Link: {user.link}"
            actions.append(
                ActionView(
                    label=f"Open {user.name}'s chat",
                    url=user.link,
                )
            )
        context_vars = "\n".join(
            f"{var.name}: {var.get()}" for var in CONTEXT_VARS
        )

        return await self.client.send(
            title=f"{title}!",
            text=(
                f"Traceback.\nContext Vars:\n{context_vars}{user_copy}"
                + ("" if self.send_file else "\n\n" + text)
            ).strip(),
            priority=5,
            actions=actions,
            file=FileAttachment(
                text.encode("utf-8"),
                "traceback.log",
            ),
        )

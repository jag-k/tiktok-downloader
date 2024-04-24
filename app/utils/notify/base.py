import asyncio
import json
import logging
from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Self, TypedDict, final

from telegram import Update

from app.constants import NOTIFY_PATH
from app.context import CallbackContext
from app.utils.text_format import camel_to_snake

logger = logging.getLogger(__name__)

__all__ = ("MessageType", "Notify")


class UserData(TypedDict, total=False):
    user: int | None
    username: str | None
    user_link: str | None


class MessageType(str, Enum):
    START = "start"
    STOP = "stop"
    SHUTDOWN = "shutdown"
    REPORT = "report"
    EXCEPTION = "exception"

    @classmethod
    def extract_from_dict(cls, obj: dict[str, str | list[str]]) -> set[Self]:
        values: dict[str, MessageType] = {
            v.value: v for v in MessageType.__members__.values()
        }
        single_type = obj.get("type", None)
        if single_type and (res := values.get(single_type, None)):
            return {res}
        return {
            item for t in obj.get("types", []) if (item := values.get(t, None))
        }


class NotifyMeta(ABCMeta):
    def __repr__(cls):
        name = getattr(cls, "service_name", cls.__name__)
        return f"Notify[{name!r}]"

    @property
    def service_name(cls):
        return getattr(cls, "SERVICE_NAME", None) or camel_to_snake(
            cls.__name__
        )

    def __getitem__(cls, item):
        return getattr(cls, "_SERVICE_REGISTRY", {})[item]


class Notify(ABC, metaclass=NotifyMeta):
    SERVICE_NAME: str | None = None
    SUPPORTED_TYPES: set[MessageType] = set()
    _SERVICES: list[Self] = []
    _SERVICE_REGISTRY: dict[str, type["Notify"]] = {}

    def __init__(self, *, types: set[MessageType] = None, **_):
        if types is None:
            types = self.SUPPORTED_TYPES.copy()
        self.types: set[MessageType] = types

    @property
    @abstractmethod
    def _is_active(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    async def _send_message(
        self,
        message_type: MessageType,
        text: str,
        update: Update | None = None,
        ctx: CallbackContext = None,
        extras: dict | None = None,
    ) -> bool:
        raise NotImplementedError()

    @classmethod
    @final
    async def send_message(
        cls,
        message_type: MessageType,
        text: str,
        update: Update | None = None,
        ctx: CallbackContext | None = None,
        extras: dict = None,
    ):
        async def error_catcher(service: Notify) -> bool:
            try:
                return await service._send_message(
                    message_type=message_type,
                    text=text,
                    update=update,
                    ctx=ctx,
                    extras=extras,
                )
            except Exception as err:
                logger.error(
                    "Error while sending notification on %r",
                    service,
                    exc_info=err,
                )
                return False

        result = await asyncio.gather(
            *[
                error_catcher(service)
                for service in cls._SERVICES
                if message_type in service.types
            ]
        )
        success_services = len(list(filter(bool, result)))
        logger.info(
            "Succeed send notifications through %d "
            "service(s) from %d service(s)",
            success_services,
            len(result),
        )
        return result

    def __init_subclass__(cls, **kwargs):
        logger.info(
            "Registering %r: %s",
            cls,
            cls.SUPPORTED_TYPES,
        )
        Notify._SERVICE_REGISTRY[cls.service_name] = cls

    @classmethod
    @final
    def load_from_json(cls) -> Self:
        if not NOTIFY_PATH.exists():
            logger.error("Can't find notification services file")
            return []
        with NOTIFY_PATH.open("r") as file:
            data: list[dict] = (json.load(file) or {}).get("services", [])
        services: list[Notify] = []
        for s in data:
            service_name: str = s.get("service", None)
            if service_name not in cls._SERVICE_REGISTRY:
                logger.error(
                    "Can't find notification service with name %r", service_name
                )
                continue
            service_type: type[Notify] = cls._SERVICE_REGISTRY[service_name]

            types: set[MessageType] = MessageType.extract_from_dict(s)
            intersection = service_type.SUPPORTED_TYPES.intersection(types)
            if not types:
                types = intersection = service_type.SUPPORTED_TYPES.copy()
            if not intersection:
                logger.error("Can't find type intersection: %r", s)
                continue

            config: dict[str, Any] = s.get("config", {})
            if "types" in config:
                del config["types"]

            try:
                service = service_type(types=types, **config)
            except TypeError as err:
                logger.error(
                    "Failed load service %r with config %r",
                    service_name,
                    config,
                    exc_info=err,
                )
                continue
            except Exception as err:
                logger.error(
                    "Failed load service %r", service_name, exc_info=err
                )
                continue

            logger.info("Successful load '%r' config", service)
            services.append(service)

        logger.info("Loaded %d notification service(s)", len(services))
        active_services = [s for s in services if s._is_active]
        cls._SERVICES = active_services
        logger.info(
            "Saved %d active service(s) from %d total",
            len(active_services),
            len(services),
        )
        return active_services

    @classmethod
    def init(cls) -> type["Notify"]:
        cls.load_from_json()
        return cls

    @staticmethod
    def _user_data_from_update(update: Update) -> UserData:
        user = update.effective_user
        return {
            "user": user.id if user else None,
            "username": user.username if user.username else None,
            "user_link": user.link if user else None,
        }

    def __repr__(self):
        return f"<{self.__class__.__name__}({', '.join(self.types)})>"


if __name__ == "__main__":
    Notify.init()

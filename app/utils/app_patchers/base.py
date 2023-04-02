import logging
from abc import ABC, abstractmethod
from typing import final

from telegram import Update
from telegram.ext import Application, BaseHandler

# noinspection PyProtectedMember
from telegram.ext._handler import RT, HandlerCallback

from app.context import CallbackContext

logger = logging.getLogger(__name__)

HandlerCallback = HandlerCallback[Update, CallbackContext, RT]
Handler = BaseHandler[Update, CallbackContext]


class Patcher(ABC):
    _PATCHERS: list[type["Patcher"]] = []
    PATCHER_NAME: str | None = None

    @classmethod
    @final
    def patch(cls, application: Application) -> Application:
        for patcher in cls._PATCHERS:
            patcher._patch_app(application)
        return application

    @staticmethod
    @abstractmethod
    def _patch(callback: HandlerCallback) -> HandlerCallback:
        raise NotImplementedError()

    @classmethod
    @final
    def name(cls) -> str:
        return cls.PATCHER_NAME or cls.__name__

    @classmethod
    @final
    def _patch_handler(cls, handler: Handler) -> Handler:
        old_callback = handler.callback
        handler.callback = cls._patch(old_callback)
        logger.info("Patched handler [%s]: %r", cls.name(), handler)
        return handler

    @classmethod
    @final
    def _patch_app(cls, application: Application) -> Application:
        old_handlers = list(application.handlers.items())
        for key, handlers in old_handlers:
            application.handlers[key] = [
                cls._patch_handler(handler) for handler in handlers
            ]
        return application

    def __init_subclass__(cls, **kwargs):
        Patcher._PATCHERS.append(cls)

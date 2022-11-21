import logging
from typing import Callable, Awaitable

from telegram import Update
from telegram.ext import BaseHandler, Application

from app.context import CallbackContext
from app.utils.i18n.base import CURRENT_LANG

HandlerCallback = Callable[[Update, CallbackContext], Awaitable]
Handler = BaseHandler[Update, CallbackContext]

__all__ = (
    'translate_patch',
    'translate_patch_handler',
    'translate_patch_app',
)

logger = logging.getLogger(__name__)


def translate_patch(func: HandlerCallback) -> HandlerCallback:
    async def wrapper(update: Update, context: CallbackContext) -> None:
        t = CURRENT_LANG.set(context.user_lang)
        try:
            return await func(update, context)
        finally:
            CURRENT_LANG.reset(t)

    return wrapper


def translate_patch_handler(handler: Handler) -> Handler:
    old_callback = handler.callback
    handler.callback = translate_patch(old_callback)
    logger.info('Patched handler: %r', handler)
    return handler


def translate_patch_app(application: Application) -> Application:
    old_dict = list(application.handlers.items())
    for key, handlers in old_dict:
        application.handlers[key] = [
            translate_patch_handler(handler)
            for handler in handlers
        ]
    return application

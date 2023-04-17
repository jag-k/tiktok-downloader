import functools

from telegram import Update

from app.context.callback_context import CallbackContext
from app.utils.app_patchers.base import HandlerCallback, Patcher
from app.utils.i18n.base import CURRENT_LANG


class I18nPatcher(Patcher):
    PATCHER_NAME = "i18n"

    @staticmethod
    def _patch(callback: HandlerCallback) -> HandlerCallback:
        @functools.wraps(callback)
        async def wrapper(update: Update, context: CallbackContext) -> None:
            t = CURRENT_LANG.set(context.user_lang)
            try:
                return await callback(update, context)
            finally:
                CURRENT_LANG.reset(t)

        return wrapper

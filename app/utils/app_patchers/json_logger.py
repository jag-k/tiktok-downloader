import functools
from contextvars import ContextVar, Token

from telegram import Update

from app.constants.json_logger import DATA_TYPE, QUERY, USER_ID, USERNAME
from app.context import CallbackContext
from app.utils.app_patchers.base import HandlerCallback, Patcher


def env_wrapper(callback: HandlerCallback) -> HandlerCallback:
    @functools.wraps(callback)
    async def wrapper(update: Update, context: CallbackContext):
        tokens: dict[ContextVar, Token] = {}

        if update.effective_user:
            tokens[USER_ID] = USER_ID.set(update.effective_user.id)
            tokens[USERNAME] = USERNAME.set(update.effective_user.username)

        if update.effective_message:
            tokens[QUERY] = QUERY.set(update.effective_message.text)
            tokens[DATA_TYPE] = DATA_TYPE.set("message")

        elif update.inline_query:
            tokens[QUERY] = QUERY.set(update.inline_query.query)
            tokens[DATA_TYPE] = DATA_TYPE.set("inline_query")

        try:
            return await callback(update, context)

        finally:
            for var, token in tokens.items():
                var.reset(token)

    return wrapper


class JsonLoggerPatcher(Patcher):
    PATCHER_NAME = "logger"

    @staticmethod
    def _patch(callback: HandlerCallback) -> HandlerCallback:
        return env_wrapper(callback)

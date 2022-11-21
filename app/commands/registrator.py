import functools
import logging
from typing import Callable

from telegram import BotCommandScopeChat, Update
from telegram.ext import CommandHandler, Application

from app.context import CallbackContext
from app.utils.i18n.base import ContextGetText

logger = logging.getLogger(__name__)

Str = str | ContextGetText


class CommandRegistrator:
    def __init__(self):
        self._command_descriptions: dict[CommandHandler, Str] = {}

    def connect_commands(self, app: Application) -> Application:
        for handler in self._command_descriptions:
            app.add_handler(handler)
            logger.info("Added commands %s to %s", handler.commands, app)
        return app

    def add(
            self,
            name: str = None,
            description: Str = None,
            auto_send_commands: bool = True,
            **kwargs
    ) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            self.add_handler(
                CommandHandler(
                    name or func.__name__,
                    func,
                    **kwargs
                ),
                description=description,
                auto_send_commands=auto_send_commands,
            )
            return func

        return decorator

    def add_handler(
            self,
            handler: CommandHandler,
            description: Str = None,
            auto_send_commands: bool = True,
    ):
        if description is None:
            description = (
                    handler.callback.__doc__ or ''
            ).strip().split('\n')[0].strip()

        old_callback = handler.callback
        command = list(handler.commands)[0]

        @functools.wraps(old_callback)
        async def wrap(update: Update, context: CallbackContext):
            logger.info('Command /%s called', command)

            res = await old_callback(update, context)

            if auto_send_commands:
                await self.send_commands(update, context)
            return res

        handler.callback = wrap
        self._command_descriptions[handler] = description
        return handler

    def get_command_description(self) -> dict[str, str]:
        return {
            list(command.commands)[0]: description
            for command, description in self._command_descriptions.items()
        }

    async def send_commands(self, update: Update, context: CallbackContext):
        commands = self.get_command_description()
        await context.bot.set_my_commands(
            commands=[
                (cmd_name, str(desc))
                for cmd_name, desc in self.get_command_description().items()
            ],
            scope=BotCommandScopeChat(update.effective_chat.id),
            language_code=update.effective_user.language_code,
        )
        logger.info(
            'Commands are sended to Chat[%s]',
            update.effective_chat.id,
        )
        return commands

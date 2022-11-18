import functools
import logging
from typing import Callable

from telegram import BotCommandScopeChat, Update
from telegram.ext import CommandHandler, Application

from app import constants
from app.context import CallbackContext

logger = logging.getLogger(__name__)


class CommandRegistrator:
    def __init__(self):
        self._command_descriptions: dict[CommandHandler, dict[str, str]] = {}

    def connect_commands(self, app: Application) -> Application:
        for handler in self._command_descriptions:
            app.add_handler(handler)
            logger.info("Added commands %s to %s", handler.commands, app)
        return app

    def add(
            self,
            name: str = None,
            description: str | dict[str, str] = None,
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
            description: str | dict[str, str] = None,
            auto_send_commands: bool = True,
    ):
        if description is None:
            description = {
                constants.DEFAULT_LOCALE: (
                        handler.callback.__doc__ or ''
                ).strip().split('\n')[0].strip()
            }
        if isinstance(description, str):
            description = {constants.DEFAULT_LOCALE: description}

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

    def get_command_description(self) -> dict[str, dict[str, str]]:
        commands = {}
        for command, descriptions in self._command_descriptions.items():
            command_name = list(command.commands)[0]
            for lang, desc in descriptions.items():
                commands.setdefault(lang, {})[command_name] = desc
        return commands

    async def send_commands(self, update: Update, context: CallbackContext):
        commands = self.get_command_description()
        logger.info(
            'Sending commands to Chat[%s]...',
            update.effective_chat.id,
        )
        for lang, commands_list in commands.items():
            lang = (
                lang
                if len(commands) > 1
                else update.effective_user.language_code
            )
            await context.bot.set_my_commands(
                commands=[
                    (cmd_name, desc)
                    for cmd_name, desc in commands_list.items()
                ],
                scope=BotCommandScopeChat(update.effective_chat.id),
                language_code=lang,
            )
            logger.info(
                'Sent commands with lang %s to Chat[%s]',
                lang,
                update.effective_chat.id
            )
        logger.info(
            'Commands are sended to Chat[%s]',
            update.effective_chat.id,
        )
        return commands

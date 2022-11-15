from typing import Callable

from telegram import BotCommandScopeChat, Update
from telegram.ext import CommandHandler, Application

from app import constants
from app.context import CallbackContext


class CommandRegistrator:
    def __init__(self):
        self._command_descriptions: dict[CommandHandler, dict[str, str]] = {}

    def connect_commands(self, application: Application) -> Application:
        for command in self._command_descriptions:
            application.add_handler(command)
        return application

    def add(
            self,
            name: str = None,
            description: str | dict[str, str] = None,
            **kwargs
    ) -> Callable[[Callable], Callable]:
        def decorator(func: Callable) -> Callable:
            self.add_handler(
                CommandHandler(
                    name or func.__name__,
                    func,
                    **kwargs
                ),
                description=description
            )
            return func

        return decorator

    def add_handler(
            self,
            handler: CommandHandler,
            description: str | dict[str, str] = None,
    ):
        if description is None:
            description = {
                constants.DEFAULT_LOCALE: (
                        handler.callback.__doc__ or ''
                ).strip().split('\n')[0].strip()
            }

        if isinstance(description, str):
            description = {constants.DEFAULT_LOCALE: description}

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
        for lang, commands_list in commands.items():
            await context.bot.set_my_commands(
                commands=[
                    (cmd_name, desc)
                    for cmd_name, desc in commands_list.items()
                ],
                scope=BotCommandScopeChat(update.effective_chat.id),
                language_code=lang,
            )
        return commands
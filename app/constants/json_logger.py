import json
import logging.config
from contextvars import ContextVar

USER_ID: ContextVar[int] = ContextVar("USER_ID", default=0)
USERNAME: ContextVar[str] = ContextVar("USERNAME", default="")
QUERY: ContextVar[str] = ContextVar("QUERY", default="")
DATA_TYPE: ContextVar[str] = ContextVar("DATA_TYPE", default="")

CONTEXT_VARS: list[ContextVar] = [
    USER_ID,
    USERNAME,
    QUERY,
    DATA_TYPE,
]

logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.

    :param fmt_dict: Key: logging format attribute pairs.
    Defaults to {"message": "message"}.

    :param time_format: time.strftime() format string.
    Default: "%Y-%m-%dT%H:%M:%S"

    :param msec_format: Microsecond formatting. Appended at the end.
    Default: "%s.%03dZ"
    """

    def __init__(
        self,
        fmt_dict: dict | None = None,
        time_format: str = "%Y-%m-%dT%H:%M:%S",
        msec_format: str = "%s.%03dZ",
    ):
        super().__init__()
        self.fmt_dict = fmt_dict or {"message": "message"}
        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    def usesTime(self) -> bool:
        """
        Overwritten to look for the attribute in the format dict values
        instead of the fmt string.
        """
        return "asctime" in self.fmt_dict.values()

    def formatMessage(self, record) -> dict:  # type: ignore[override]
        """
        Overwritten to return a dictionary of the relevant LogRecord attributes
        instead of a string.
        KeyError is raised if an unknown attribute is provided in the fmt_dict.
        """
        return {fmt_key: record.__dict__[fmt_val] for fmt_key, fmt_val in self.fmt_dict.items()}

    def format(self, record) -> str:
        """
        Mostly the same as the parent's class method, the difference
        being that a dict is manipulated and dumped as JSON
        instead of a string.
        """
        record.message = record.getMessage()

        if self.usesTime():
            setattr(record, "asctime", self.formatTime(record, self.datefmt))

        message_dict = self.formatMessage(record)

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            message_dict["exc_info"] = record.exc_text

        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        for context_var in CONTEXT_VARS:
            message_dict[context_var.name.lower()] = context_var.get() or None

        return json.dumps(message_dict, default=str)

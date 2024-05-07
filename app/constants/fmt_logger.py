import json

from .json_logger import JsonFormatter

__all__ = ("FmtFormatter",)


def escape_string(string: str) -> str:
    if " " in string or '"' in string or "'" in string:
        return json.dumps(string)
    return string


class FmtFormatter(JsonFormatter):
    def format(self, record) -> str:
        """
        Mostly the same as the parent's class method, the difference
        being that a dict is manipulated and dumped as JSON
        instead of a string.
        """
        message_dict: dict[str, str] = json.loads(super().format(record))

        return " ".join(f"{k}={escape_string(v)}" for k, v in message_dict.items() if v)

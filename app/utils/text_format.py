def a(text: str, url: str | None = None) -> str:
    if url:
        return f'<a href="{url}">{text}</a>'
    return text


def b(text: str) -> str:
    return f"<b>{text}</b>"


def i(text: str) -> str:
    return f"<i>{text}</i>"


def u(text: str) -> str:
    return f"<u>{text}</u>"


def camel_to_snake(s: str) -> str:
    """
    Convert CamelCase string `s` to snake_case.
    """
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")

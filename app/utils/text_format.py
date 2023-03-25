def a(text: str, url: str = None) -> str:
    if url:
        return f'<a href="{url}">{text}</a>'
    return text


def b(text: str) -> str:
    return f"<b>{text}</b>"


def i(text: str) -> str:
    return f"<i>{text}</i>"


def u(text: str) -> str:
    return f"<u>{text}</u>"

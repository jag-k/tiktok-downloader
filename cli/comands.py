import logging
from collections.abc import Callable

from constants import BASE_PATH

from app.constants import DEFAULT_LOCALE
from cli.compile import main as compile_locale
from cli.extract import main as extract_locale
from cli.update import main as update_locale

commands: dict[str, Callable] = {}

logger = logging.getLogger(__name__)


def add_command(
    name: str | None = None,
    func: Callable | None = None,
    *,
    description: str | None = None,
    extra: str | None = None,
) -> Callable:
    def decorator(f: Callable) -> Callable:
        nonlocal name
        if name is None:
            name = f.__name__

        if description is not None:
            f.__doc__ = description

        if extra is not None:
            f.__extra__ = extra

        commands[name] = f
        return f

    if func is not None:
        return decorator(func)

    return decorator


def markdown_update_region(markdown: str, region: str, data: str) -> str:
    start = f"<!--region:{region}-->"
    end = f"<!--endregion:{region}-->"

    if start not in markdown:
        logger.error("No region %r found in markdown", start)
        return markdown

    start_rm, text = markdown.split(start, 1)
    if end not in text:
        logger.error("No region %r found in markdown", end)
        return markdown

    end_rm = markdown.split(end, 1)[1]
    logger.info("Update %r region in markdown", region)

    return f"{start_rm.strip()}\n\n" f"{start}\n\n" f"{data.strip()}\n\n" f"{end}\n\n" f"{end_rm.strip()}"


add_command(
    "compile_locale",
    compile_locale,
    description="Extract strings from code to .POT file",
)
add_command(
    "extract_locale",
    extract_locale,
    description="Update .PO file for Russian language",
    extra="-l ru",
)
add_command(
    "update_locale",
    update_locale,
    description="Extract strings and update .PO file for Russian language",
    extra="-l ru",
)


@add_command(description="Compile .PO files to .MO files")
def full_update_locale(lang: str = DEFAULT_LOCALE) -> None:
    extract_locale()
    update_locale(lang)


@add_command(description="Generate Makefile")
def generate_makefile() -> list[dict]:
    makefile = BASE_PATH / "Makefile"

    data = [
        {
            "name": name,
            "description": description,
            "extra": extra,
        }
        for name, func in commands.items()
        if (description := f"  # {func.__doc__}" if func.__doc__ else "") or True
        if (extra := f" {func.__extra__}" if hasattr(func, "__extra__") else "") or True
    ]

    # noinspection PyTypeChecker,PydanticTypeChecker
    cmds = "\n".join(
        f"{name}:{description}\n" f"\tpoetry run -- python -m cli {name}{extra}\n"
        for name, description, extra in map(dict.values, data)
    )

    makefile.write_text(
        "# This file is generated by cli/commands.py\n"
        "# Do not edit this file directly\n"
        "# Run `poetry run -- python -m cli generate_makefile` "
        "to update this file\n\n"
        f"{cmds}"
    )
    return data


@add_command(description="Generate Makefile and update README.md")
def generate_makefile_md() -> None:
    data = generate_makefile()
    text = "```bash"
    # noinspection PyTypeChecker,PydanticTypeChecker
    for name, description, extra in map(dict.values, data):
        text += f"\nmake {name}{description}"
    text += "\n```"
    readme_file = BASE_PATH / "README.md"
    readme = readme_file.read_text()
    readme = markdown_update_region(readme, "makefile", text)
    readme_file.write_text(readme.strip() + "\n")
    print("README.md updated")


@add_command(description="Full update README.md")
def full_update_readme() -> None:
    generate_makefile_md()

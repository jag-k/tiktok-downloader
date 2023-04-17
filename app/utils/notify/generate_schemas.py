import inspect
from pathlib import Path

from app.constants import BASE_PATH
from app.utils.notify.base import Notify

type_mapping = {
    str: "string",
    bool: "boolean",
    float: "number",
    int: "integer",
    list: "array",
    tuple: "array",
    dict: "object",
    type(None): "null",
}


def type_map(cls: type, default: str = "string"):
    for k, v in type_mapping.items():
        if issubclass(cls, k):
            return v
    return default


def generate_jsonschema():
    # region Making types a recursive schema
    # noinspection PyProtectedMember
    registry = Notify._SERVICE_REGISTRY

    conditionals: list[dict] = []

    for service, cls in registry.items():
        props = {
            k: {
                "type": type_map(v, "string"),
            }
            for k, v in inspect.get_annotations(cls.__init__).items()
            if k != "return"
            if k != "types"
        }

        full_spec = inspect.getfullargspec(cls.__init__)
        have_default = set(full_spec.kwonlydefaults)
        required_props = [k for k in props.keys() if k not in have_default]
        config = {
            "type": "object",
            "additionalProperties": False,
            "properties": props,
        }
        if required_props:
            config["required"] = required_props

        for k, v in full_spec.kwonlydefaults.items():
            if k == "types":
                continue
            if isinstance(v, Path):
                v = v.relative_to(BASE_PATH)
            config["properties"][k]["default"] = v
            config["properties"][k]["example"] = v

        conditionals.append(
            {
                "if": {"properties": {"service": {"const": service}}},
                "then": {
                    "properties": {
                        "types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    t.value for t in sorted(cls.SUPPORTED_TYPES)
                                ],
                            },
                        },
                        "config": config,
                    }
                },
            }
        )

    result = {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "enum": list(registry.keys()),
            },
        },
        "required": ["service"],
        "allOf": conditionals,
    }

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Notify config schema",
        "description": "Schema for notify config",
        "type": "object",
        "properties": {
            "services": {"type": "array", "items": result},
        },
    }


def generate_md_table(headers: list[str], data: list[list[str]]) -> str:
    # Determine maximum length of values in each column
    max_lengths = [len(str(header)) for header in headers]
    for row in data:
        for i, value in enumerate(row):
            max_lengths[i] = max(max_lengths[i], len(str(value)))

    # Generate table header
    header_row = (
        "| "
        + " | ".join(
            header.ljust(max_lengths[i]) for i, header in enumerate(headers)
        )
        + " |"
    )
    separator_row = (
        "|"
        + "-|".join("-" * (max_lengths[i] + 1) for i in range(len(headers)))
        + "-|"
    )

    # Generate table rows
    data_rows = [
        "| "
        + " | ".join(
            str(value).ljust(max_lengths[i]) for i, value in enumerate(row)
        )
        + " |"
        for row in data
    ]

    # Combine header, separator, and data rows into final table
    table = "\n".join([header_row, separator_row] + data_rows)

    return table


def generate_markdown() -> str:
    # noinspection PyProtectedMember
    registry = Notify._SERVICE_REGISTRY

    def required(value: bool) -> str:
        return "✅ True" if value else "❌ False"

    result: list[str] = []
    for module_name, module in registry.items():
        module_str = f"#### Module `{module_name}`\n\n"

        doc = [s for i in module.__doc__.split("\n") if (s := i.strip())]
        description = [i for i in doc if not i.startswith(":")]
        module_str += "\n".join(description) + "\n\n"

        config = [i for i in doc if i.startswith(":")]
        config_dict = {}
        for c in config:
            t, param, desc = c.split(" ", 2)
            t = t[1:]
            param = param[:-1]
            if t == "param":
                config_dict.setdefault(
                    param,
                    {
                        "description": "",
                        "default": "",
                    },
                )["description"] = desc
            elif t == "default":
                config_dict.setdefault(
                    param,
                    {
                        "description": "",
                        "default": "",
                    },
                )["default"] = desc

        if not config_dict:
            continue
        module_str += "Config:\n\n"
        module_str += generate_md_table(
            ["Name", "Description", "Default value", "Required"],
            [
                [
                    f"`{param}`",
                    data["description"],
                    default,
                    required(not data["default"]),
                ]
                for param, data in config_dict.items()
                if (d := data["default"]) or True
                if (default := f"`{d}`" if d else "") or True
            ],
        )
        result.append(module_str)

    return "\n\n".join(result)


if __name__ == "__main__":
    import json

    print(json.dumps(generate_jsonschema(), indent=2, default=str))
    print(generate_markdown())

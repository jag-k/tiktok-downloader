import json

from pydantic import BaseModel, ConfigDict, Field

__all__ = ("Model",)

json_encoders = {}


class Model(BaseModel):
    model_config = ConfigDict(json_encoders=json_encoders)

    type_: str | None = Field(None, alias="@type", exclude=True, repr=False, allow_mutation=False)

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        models: dict[str, type[Model]] | None = getattr(Model, "MODELS", {})
        if not models:
            setattr(Model, "MODELS", models)
        models[cls.__name__] = cls

    def to_dict(self) -> dict:
        d = json.loads(
            self.model_dump_json(
                exclude_defaults=True,
                exclude_none=True,
                exclude_unset=True,
            )
        )
        d["@type"] = self.__class__.__name__
        return d

    @classmethod
    def from_dict(cls, value: dict) -> "Model":
        """Create an instance of the Model class from a dictionary.

        :param value: A dictionary containing the data for the model.
        :return: An instance of the Model class.
        """
        models: dict[str, type[Model]] = getattr(Model, "MODELS", {})
        type_: str | None = dict(value).pop("@type", None)
        return models.get(type_, cls).model_validate(value)


json_encoders |= {
    Model: lambda v: v.to_dict(),
}

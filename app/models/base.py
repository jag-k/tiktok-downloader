from typing import Self

from pydantic import BaseModel, Field


class Model(BaseModel):
    _type = Field(
        None, alias="@type", exclude=True, repr=False, allow_mutation=False
    )

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        models: dict[str, type[Model]] | None = getattr(Model, "MODELS", None)
        if models is None:
            models = {}
            setattr(Model, "MODELS", models)
        models[cls.__name__] = cls

    def to_dict(self) -> dict:
        def encoder(v):
            if isinstance(v, Model):
                return v.to_dict()
            return v

        d = self.__config__.json_loads(
            self.json(
                exclude_defaults=True,
                exclude_none=True,
                exclude_unset=True,
                encoder=encoder,
            )
        )
        d["@type"] = self.__class__.__name__
        return d

    @classmethod
    def from_dict(cls, value: dict) -> Self:
        models: dict[str, type[Model]] = getattr(Model, "MODELS", {})
        type_ = value.pop("@type", None)
        return models.get(type_, cls)(**value)

    class Config:
        json_encoders = {
            "Model": lambda v: v.to_dict(),
        }

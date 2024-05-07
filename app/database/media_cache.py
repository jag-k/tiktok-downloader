from datetime import datetime

import pytz
from motor.motor_asyncio import AsyncIOMotorCollection as Collection

from app.database.connector import MongoDatabase
from app.models.medias import Media


class MediaCache(MongoDatabase):
    @classmethod
    async def col(cls) -> Collection | None:
        if cls._db is None:
            return None

        name = "media_cache"

        return await cls._get_col(name)

    @classmethod
    async def get_medias(cls, original_url: str) -> list[Media] | None:
        col = await cls.col()
        if col is None:
            return None

        data = await col.find_one({"_id": original_url})
        if not data:
            return None
        d = dict(data)
        d.pop("_id", None)
        d.pop("created_at", None)
        d.pop("updated_at", None)
        return [Media.from_dict(i) for i in d.get("content", [])]

    @classmethod
    async def save_medias(cls, *medias: Media) -> str | None:
        if not medias:
            return None

        col: Collection = await cls.col()
        if col is None:
            return None

        now = datetime.now(tz=pytz.UTC)
        url = medias[0].original_url
        data = [m.to_dict() for m in medias]

        old = await col.find_one({"_id": url})
        print("save_medias", url, old)
        if old:
            res = await col.update_one(
                {"_id": url},
                {
                    "$set": {
                        "content": old.get("data", []) + data,
                        "updated_at": now,
                    }
                },
            )
        else:
            res = await col.insert_one(
                {
                    "_id": url,
                    "created_at": now,
                    "updated_at": now,
                    "content": data,
                }
            )
        return str(res.inserted_id)

    @classmethod
    async def update_medias(cls, original_url: str, *medias: Media) -> None:
        if not cls._db:
            return None
        col = await cls.col()
        await col.update_one(
            {"_id": original_url},
            {
                "content": [m.to_dict() for m in medias],
                "updated_at": datetime.now(tz=pytz.UTC),
            },
        )

    @classmethod
    async def delete_media(cls, original_url: str) -> None:
        col = await cls.col()
        if col is None:
            return None
        await col.delete_one({"_id": original_url})

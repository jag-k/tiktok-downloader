from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo.errors import CollectionInvalid

from app.database.connector import MongoDatabase
from app.models.medias import Media


class MediaCache(MongoDatabase):
    _collection: Collection = None

    @classmethod
    async def col(cls) -> Collection | None:
        if cls._db is None:
            return

        name = "media_cache"
        if cls._collection is not None:
            return cls._collection
        try:
            cls._collection = await cls._db.create_collection(name)
        except CollectionInvalid as e:
            if e.args[0] != f"collection {name} already exists":
                raise e
            cls._collection = cls._db.get_collection(name)
        return cls._collection

    @classmethod
    async def get_medias(cls, original_url: str) -> list[Media] | None:
        col = await cls.col()
        if col is None:
            return

        data = await col.find_one({"_id": original_url})
        if not data:
            return
        d = dict(data)
        d.pop("_id", None)
        d.pop("created_at", None)
        d.pop("updated_at", None)
        return [Media.from_dict(i) for i in d.get("content", [])]

    @classmethod
    async def save_medias(cls, *medias: Media) -> str | None:
        col: Collection = await cls.col()
        if col is None:
            return
        now = datetime.utcnow()
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
            return
        col = await cls.col()
        await col.update_one(
            {"_id": original_url},
            {
                "content": [m.to_dict() for m in medias],
                "updated_at": datetime.utcnow(),
            },
        )

    @classmethod
    async def delete_media(cls, original_url: str) -> None:
        col = await cls.col()
        if not col:
            return
        await col.delete_one({"_id": original_url})

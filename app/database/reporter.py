import asyncio
from datetime import datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo.errors import OperationFailure

from app.context import CallbackContext
from app.database.connector import MongoDatabase
from app.models.report import Report


class Reporter(MongoDatabase):
    _collection: Collection | None = None

    @classmethod
    async def col(cls) -> Collection | None:
        if cls._db is None:
            return None

        name = "reports"
        await cls._get_col(name)

        # Авто удаление старых записей
        index_name = "created_at_ttl"
        expire_after_seconds = 1800  # 30 минут
        try:
            # Попытка создания индекса
            await cls._collection.create_index(
                "created_at",
                expireAfterSeconds=expire_after_seconds,
                name=index_name,
            )
        except OperationFailure as e:
            # Если индекс уже существует, удаляем его и создаем новый
            if e.code == 85:
                await cls._collection.drop_index(index_name)
                await cls._collection.create_index(
                    "created_at",
                    expireAfterSeconds=expire_after_seconds,
                    name=index_name,
                )
            else:
                raise e

        return cls._collection

    @classmethod
    async def get_report(cls, report_id: str) -> Report | None:
        col = await cls.col()
        if col is None:
            return None

        data = await col.find_one({"_id": ObjectId(report_id)})
        if not data:
            return None
        d = dict(data)
        d.pop("_id", None)
        d.pop("created_at", None)
        d.pop("updated_at", None)
        return Report.from_dict(d)

    @classmethod
    async def save_report(cls, report: Report) -> str | None:
        col = await cls.col()
        if col is None:
            return None

        now = datetime.utcnow()
        data = report.to_dict()
        data.pop("@type")
        res = await col.insert_one(
            {
                "created_at": now,
                "updated_at": now,
                **data,
            }
        )
        return str(res.inserted_id)

    @classmethod
    async def update_report(cls, report_id: str, report: Report) -> None:
        if not cls._db:
            return None
        col = await cls.col()
        await col.update_one(
            {"_id": report_id},
            {**report.to_dict(), "updated_at": datetime.utcnow()},
        )

    @classmethod
    async def delete_report(cls, report_id: str) -> None:
        col = await cls.col()
        if col is not None:
            return None
        await col.delete_one({"_id": report_id})

    @classmethod
    async def from_context(cls, ctx: CallbackContext) -> list[Report]:
        return await asyncio.gather(*(cls.get_report(arg[7:]) for arg in (ctx.args or []) if arg.startswith("report_")))

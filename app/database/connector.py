from motor.motor_asyncio import AsyncIOMotorClient as Client
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from motor.motor_asyncio import AsyncIOMotorDatabase as Database
from pymongo.errors import CollectionInvalid

from app import constants

_client: Client | None = None
_db: Database | None = None


class MongoDatabase:
    _client: Client | None = None
    _db: Database | None = None
    _collection: Collection | None = None

    @classmethod
    def init(cls) -> None:
        cls._client = Client(constants.MONGO_URL)
        cls._db = cls._client.get_database(constants.MONGO_DB)
        for sub_cls in cls.__subclasses__():
            sub_cls._client = cls._client
            sub_cls._db = cls._db

    @classmethod
    def close(cls) -> None:
        cls._client.close()

    @classmethod
    async def _get_col(cls, name: str) -> Collection | None:
        if cls._collection is not None:
            return cls._collection
        try:
            cls._collection = await cls._db.create_collection(name)
        except CollectionInvalid as e:
            if e.args[0] != f"collection {name} already exists":
                raise e
            cls._collection = cls._db.get_collection(name)
        return cls._collection

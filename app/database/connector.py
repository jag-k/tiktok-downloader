from motor.motor_asyncio import AsyncIOMotorClient as Client
from motor.motor_asyncio import AsyncIOMotorDatabase as Database

from app import constants

_client: Client = None
_db: Database = None


class MongoDatabase:
    _client: Client = None
    _db: Database = None

    @classmethod
    def init(cls):
        cls._client = Client(constants.MONGO_URL)
        cls._db = cls._client.get_database(constants.MONGO_DB)
        for sub_cls in cls.__subclasses__():
            sub_cls._client = cls._client
            sub_cls._db = cls._db

    @classmethod
    def close(cls):
        cls._client.close()

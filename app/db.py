import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import config

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    
    @classmethod
    async def connect(cls):
        """Подключение к MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(config.MONGO_URI)
            # Проверяем подключение
            await cls.client.admin.command('ping')
            cls.db = cls.client[config.DB_NAME]
            
            await cls.create_indexes()
            print("✅ Подключено к MongoDB")
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            print(f"   Проверьте URI: {config.MONGO_URI}")
            raise
    
    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            print("👋 Отключено от MongoDB")
    
    @classmethod
    async def create_indexes(cls):
        """Создание индексов с обработкой ошибок"""
        try:
            # Проверяем, существует ли коллекция
            collections = await cls.db.list_collection_names()
            
            # Создаем индексы для сотрудников
            if config.COLL_EMPLOYEES not in collections:
                await cls.db.create_collection(config.COLL_EMPLOYEES)
            
            await cls.db[config.COLL_EMPLOYEES].create_index("full_name")
            await cls.db[config.COLL_EMPLOYEES].create_index("department")
            
            # Создаем индексы для заявок
            if config.COLL_TICKETS not in collections:
                await cls.db.create_collection(config.COLL_TICKETS)
            
            # await cls.db[config.COLL_TICKETS].create_index("number", unique=True)
            await cls.db[config.COLL_TICKETS].create_index("status")
            await cls.db[config.COLL_TICKETS].create_index("executor_id")
            await cls.db[config.COLL_TICKETS].create_index("deadline")
            await cls.db[config.COLL_TICKETS].create_index("author_id")
            await cls.db[config.COLL_TICKETS].create_index([
                ("executor_id", 1),
                ("status", 1),
                ("deadline", 1)
            ])
            
            print("✅ Индексы созданы")
        except Exception as e:
            print(f"⚠️ Ошибка при создании индексов: {e}")
            # Продолжаем работу даже если индексы не создались
    
    @classmethod
    def get_collection(cls, name: str):
        return cls.db[name]

db = Database()
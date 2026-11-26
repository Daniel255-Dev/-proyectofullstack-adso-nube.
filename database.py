from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = str(config("MONGODB_URL", default="mongodb://localhost:27017"))
DATABASE_NAME = str(config("DATABASE_NAME", default="adso_db"))

client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

coleccion_tareas = database["tareas"]


async def verificar_conexion():
    try:
        await client.server_info()  # Verifica la conexión al servidor MongoDB
        print(f"Conexión a MongoDB exitosa - Base de datos: '{DATABASE_NAME}'")
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")

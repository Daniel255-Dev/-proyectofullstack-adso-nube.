from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List

from bson import ObjectId
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import coleccion_tareas, verificar_conexion
from models import Tarea, TareaCreate, TareaUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    await verificar_conexion()
    mongo_database = coleccion_tareas.database
    collection_name = coleccion_tareas.name
    if collection_name not in await mongo_database.list_collection_names():
        await mongo_database.create_collection(collection_name)
    yield


app = FastAPI(
    title="API TODO App Profesional - SENA ADSO",
    description="API RESTful asincrona con FastAPI y MongoDB (FARM Stack).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cliente_dir = Path(__file__).resolve().parent / "cliente_todo_app"
app.mount("/cliente", StaticFiles(directory=cliente_dir, html=True), name="cliente")


@app.get("/", tags=["Raiz"])
async def root():
    return {
        "mensaje": "Bienvenido a la API TODO App Asincrona con MongoDB",
        "documentacion": "/docs",
    }


@app.post(
    "/tareas",
    response_model=Tarea,
    status_code=status.HTTP_201_CREATED,
    tags=["Tareas"],
    summary="Crear una nueva tarea en MongoDB",
)
async def create_tarea(tarea_in: TareaCreate):
    tarea_existente = await coleccion_tareas.find_one({"titulo": tarea_in.titulo})
    if tarea_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una tarea registrada con el titulo '{tarea_in.titulo}'.",
        )

    nueva_tarea = tarea_in.model_dump()
    nueva_tarea["fecha_creacion"] = datetime.now()
    resultado = await coleccion_tareas.insert_one(nueva_tarea)
    tarea_creada = await coleccion_tareas.find_one({"_id": resultado.inserted_id})
    if tarea_creada is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible recuperar la tarea recien creada.",
        )
    return tarea_creada


@app.get(
    "/tareas",
    response_model=List[Tarea],
    status_code=status.HTTP_200_OK,
    tags=["Tareas"],
    summary="Listar todas las tareas",
)
async def get_tareas():
    tareas = []
    cursor = coleccion_tareas.find()
    async for documento in cursor:
        tareas.append(documento)
    return tareas


@app.get(
    "/tareas/{id}",
    response_model=Tarea,
    status_code=status.HTTP_200_OK,
    tags=["Tareas"],
    summary="Buscar tarea por ObjectId",
)
async def get_tarea_por_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId valido de MongoDB.",
        )

    tarea = await coleccion_tareas.find_one({"_id": ObjectId(id)})
    if tarea is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La tarea con ID '{id}' no fue encontrada en la base de datos.",
        )
    return tarea


@app.put(
    "/tareas/{id}",
    response_model=Tarea,
    status_code=status.HTTP_200_OK,
    tags=["Tareas"],
    summary="Actualizar estado o campos de una tarea",
)
async def update_tarea(id: str, tarea_update: TareaUpdate):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId valido.",
        )

    object_id = ObjectId(id)
    datos_a_actualizar = tarea_update.model_dump(exclude_unset=True)

    if datos_a_actualizar:
        resultado_actualizacion = await coleccion_tareas.update_one(
            {"_id": object_id},
            {"$set": datos_a_actualizar},
        )
        if resultado_actualizacion.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe una tarea con el ID '{id}'.",
            )

    tarea_actualizada = await coleccion_tareas.find_one({"_id": object_id})
    if tarea_actualizada is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe una tarea con el ID '{id}'.",
        )
    return tarea_actualizada


@app.delete(
    "/tareas/{id}",
    status_code=status.HTTP_200_OK,
    tags=["Tareas"],
    summary="Eliminar tarea de MongoDB",
)
async def delete_tarea(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId valido.",
        )

    resultado_eliminacion = await coleccion_tareas.delete_one({"_id": ObjectId(id)})
    if resultado_eliminacion.deleted_count == 1:
        return {"mensaje": f"Tarea con ID '{id}' eliminada exitosamente de MongoDB."}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No fue posible eliminar. La tarea con ID '{id}' no existe.",
    )

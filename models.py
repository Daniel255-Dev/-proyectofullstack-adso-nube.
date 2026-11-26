from datetime import datetime
from typing import Annotated, Optional

from bson import ObjectId
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from pydantic_core import core_schema


class _ObjectIDPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(v):
            if isinstance(v, ObjectId):
                return str(v)
            if isinstance(v, str) and ObjectId.is_valid(v):
                return v
            raise ValueError("ID invalido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


pyObjectId = Annotated[str, _ObjectIDPydanticAnnotation()]


class TareaBase(BaseModel):
    titulo: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Titulo descriptivo de la tarea",
        examples=["Diseñar la arquitectura del proyecto FARM stack"],
    )
    description: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("description", "descripcion"),
        min_length=3,
        max_length=500,
        description="Detalles adicionales o requerimientos",
        examples=["Definir los modelos de pydantic y las rutas en FastAPI"],
    )
    completada: bool = Field(
        default=False,
        description="Estado de cumplimiento de la tarea",
    )


class TareaCreate(TareaBase):
    pass


class TareaUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    completada: Optional[bool] = None


class Tarea(TareaBase):
    id: pyObjectId = Field(
        alias="_id", description="identificador unico ObjectId de MongoDB"
    )
    fecha_creacion: datetime = Field(
        default_factory=datetime.now, description="Fecha de registro"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "654321abcdef012345678",
                "titulo": "Implentar endpoints asincronos",
                "description": "Uso de async/await con el driver Motor",
                "completada": False,
                "fecha_creacion": "2026-11-05T18:30:00",
            }
        },
    )

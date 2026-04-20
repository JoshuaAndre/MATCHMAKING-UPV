from uuid import uuid4
from typing import List

from fastapi import FastAPI, HTTPException, Depends, Path
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import Player

COMMON_SWAGGER_CONFIG = {
    "deepLinking": True,
    "displayRequestDuration": True,
    "docExpansion": "list",
    "defaultModelsExpandDepth": 1,
    "defaultModelExpandDepth": 2,
}

app = FastAPI(
    title="MATCHMAKING-UPV | Player Service",
    summary="Servicio de gestión de jugadores",
    description="""
Microservicio encargado de registrar, consultar y actualizar jugadores dentro de la plataforma de matchmaking basada en MMR.
""",
    version="2.0.0",
    swagger_ui_parameters=COMMON_SWAGGER_CONFIG,
    openapi_tags=[
        {"name": "health", "description": "Verificación de estado del servicio."},
        {"name": "players", "description": "Operaciones relacionadas con jugadores."},
    ],
)


class HealthResponse(BaseModel):
    status: str = Field(description="Estado general del servicio", examples=["ok"])
    service: str = Field(description="Nombre técnico del servicio", examples=["player-service"])


class PlayerCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="Nombre único del jugador.")
    mmr: int = Field(default=1000, ge=0, description="MMR inicial del jugador.")
    region: str = Field(default="mx", description="Región principal del jugador.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "JoshuaPlayer",
                "mmr": 1200,
                "region": "mx"
            }
        }
    )


class PlayerResponse(BaseModel):
    id: str
    username: str
    mmr: int
    region: str

    model_config = ConfigDict(from_attributes=True)


class PlayerMMRUpdate(BaseModel):
    mmr: int = Field(..., ge=0, description="Nuevo MMR del jugador")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mmr": 1215
            }
        }
    )


class ErrorResponse(BaseModel):
    detail: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"], response_model=HealthResponse)
def health():
    return {"status": "ok", "service": "player-service"}


@app.post(
    "/players",
    tags=["players"],
    response_model=PlayerResponse,
    status_code=201,
    responses={400: {"model": ErrorResponse}}
)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    existing_player = db.query(Player).filter(Player.username.ilike(player.username)).first()
    if existing_player:
        raise HTTPException(status_code=400, detail="El username ya existe")

    new_player = Player(
        id=str(uuid4()),
        username=player.username,
        mmr=player.mmr,
        region=player.region
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player


@app.get("/players", tags=["players"], response_model=List[PlayerResponse])
def list_players(db: Session = Depends(get_db)):
    return db.query(Player).all()


@app.get(
    "/players/{player_id}",
    tags=["players"],
    response_model=PlayerResponse,
    responses={404: {"model": ErrorResponse}}
)
def get_player(
    player_id: str = Path(..., description="ID único del jugador"),
    db: Session = Depends(get_db)
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player


@app.put(
    "/players/{player_id}/mmr",
    tags=["players"],
    response_model=PlayerResponse,
    responses={404: {"model": ErrorResponse}}
)
def update_player_mmr(player_id: str, payload: PlayerMMRUpdate, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    player.mmr = payload.mmr
    db.commit()
    db.refresh(player)
    return player
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List
from uuid import uuid4

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
    version="1.2.0",
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


class PlayerMMRUpdate(BaseModel):
    mmr: int = Field(..., ge=0, description="Nuevo MMR del jugador")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mmr": 1216
            }
        }
    )


class ErrorResponse(BaseModel):
    detail: str


players_db: Dict[str, PlayerResponse] = {}


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
def create_player(player: PlayerCreate):
    for existing_player in players_db.values():
        if existing_player.username.lower() == player.username.lower():
            raise HTTPException(status_code=400, detail="El username ya existe")

    player_id = str(uuid4())
    new_player = PlayerResponse(
        id=player_id,
        username=player.username,
        mmr=player.mmr,
        region=player.region
    )
    players_db[player_id] = new_player
    return new_player


@app.get("/players", tags=["players"], response_model=List[PlayerResponse])
def list_players():
    return list(players_db.values())


@app.get(
    "/players/{player_id}",
    tags=["players"],
    response_model=PlayerResponse,
    responses={404: {"model": ErrorResponse}}
)
def get_player(
    player_id: str = Path(..., description="ID único del jugador")
):
    player = players_db.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player


@app.put(
    "/players/{player_id}/mmr",
    tags=["players"],
    response_model=PlayerResponse,
    responses={404: {"model": ErrorResponse}}
)
def update_player_mmr(player_id: str, payload: PlayerMMRUpdate):
    player = players_db.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    updated = PlayerResponse(
        id=player.id,
        username=player.username,
        mmr=payload.mmr,
        region=player.region
    )
    players_db[player_id] = updated
    return updated
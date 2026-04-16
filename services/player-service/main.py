from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
from uuid import uuid4

app = FastAPI(
    title="Player Service",
    description="Microservicio para gestión básica de jugadores",
    version="1.0.0"
)


class PlayerCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    mmr: int = Field(default=1000, ge=0)
    region: str = Field(default="mx")


class PlayerResponse(BaseModel):
    id: str
    username: str
    mmr: int
    region: str


# Base temporal en memoria
players_db: Dict[str, PlayerResponse] = {}


@app.get("/health")
def health():
    return {"status": "ok", "service": "player-service"}


@app.post("/players", response_model=PlayerResponse, status_code=201)
def create_player(player: PlayerCreate):
    # Validar username único
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


@app.get("/players", response_model=List[PlayerResponse])
def list_players():
    return list(players_db.values())


@app.get("/players/{player_id}", response_model=PlayerResponse)
def get_player(player_id: str):
    player = players_db.get(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player   
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional
from uuid import uuid4
import httpx
import os

app = FastAPI(
    title="MATCHMAKING-UPV | Match Service",
    summary="Servicio de gestión de partidas",
    description="Crea partidas, las finaliza y actualiza MMR usando rating-service y player-service.",
    version="1.2.0",
    openapi_tags=[
        {"name": "health", "description": "Estado del servicio."},
        {"name": "matches", "description": "Gestión de partidas."},
    ]
)

RATING_SERVICE_URL = os.getenv("RATING_SERVICE_URL", "http://rating-service:8000")
PLAYER_SERVICE_URL = os.getenv("PLAYER_SERVICE_URL", "http://player-service:8000")


class MatchCreate(BaseModel):
    player1_id: str
    player1_mmr: int = Field(..., ge=0)
    player2_id: str
    player2_mmr: int = Field(..., ge=0)
    region: str = Field(default="mx")
    mode: str = Field(default="1v1")


class MatchResponse(BaseModel):
    id: str
    player1_id: str
    player1_mmr: int
    player2_id: str
    player2_mmr: int
    region: str
    mode: str
    status: Literal["pending", "finished"]
    winner_id: Optional[str] = None
    player1_new_mmr: Optional[int] = None
    player2_new_mmr: Optional[int] = None


class MatchFinishRequest(BaseModel):
    winner_id: str


matches_db: Dict[str, MatchResponse] = {}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "match-service"}


@app.post("/matches", tags=["matches"], response_model=MatchResponse, status_code=201)
def create_match(data: MatchCreate):
    if data.player1_id == data.player2_id:
        raise HTTPException(status_code=400, detail="Los jugadores deben ser diferentes")

    match_id = str(uuid4())
    match = MatchResponse(
        id=match_id,
        player1_id=data.player1_id,
        player1_mmr=data.player1_mmr,
        player2_id=data.player2_id,
        player2_mmr=data.player2_mmr,
        region=data.region,
        mode=data.mode,
        status="pending",
        winner_id=None,
        player1_new_mmr=None,
        player2_new_mmr=None
    )
    matches_db[match_id] = match
    return match


@app.get("/matches", tags=["matches"], response_model=List[MatchResponse])
def list_matches():
    return list(matches_db.values())


@app.get("/matches/{match_id}", tags=["matches"], response_model=MatchResponse)
def get_match(match_id: str):
    match = matches_db.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return match


@app.patch("/matches/{match_id}/finish", tags=["matches"], response_model=MatchResponse)
def finish_match(match_id: str, data: MatchFinishRequest):
    match = matches_db.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    if match.status == "finished":
        raise HTTPException(status_code=400, detail="La partida ya fue finalizada")

    if data.winner_id not in [match.player1_id, match.player2_id]:
        raise HTTPException(status_code=400, detail="El ganador no pertenece a esta partida")

    try:
        rating_response = httpx.post(
            f"{RATING_SERVICE_URL}/calculate",
            json={
                "player1_id": match.player1_id,
                "player1_mmr": match.player1_mmr,
                "player2_id": match.player2_id,
                "player2_mmr": match.player2_mmr,
                "winner_id": data.winner_id,
                "k_factor": 32
            },
            timeout=10.0
        )
        rating_response.raise_for_status()
        rating_data = rating_response.json()

        httpx.put(
            f"{PLAYER_SERVICE_URL}/players/{match.player1_id}/mmr",
            json={"mmr": rating_data["new_player1_mmr"]},
            timeout=10.0
        ).raise_for_status()

        httpx.put(
            f"{PLAYER_SERVICE_URL}/players/{match.player2_id}/mmr",
            json={"mmr": rating_data["new_player2_mmr"]},
            timeout=10.0
        ).raise_for_status()

    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="No se pudo conectar con rating-service o player-service")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error en servicio interno: {e.response.text}")

    updated_match = MatchResponse(
        id=match.id,
        player1_id=match.player1_id,
        player1_mmr=match.player1_mmr,
        player2_id=match.player2_id,
        player2_mmr=match.player2_mmr,
        region=match.region,
        mode=match.mode,
        status="finished",
        winner_id=data.winner_id,
        player1_new_mmr=rating_data["new_player1_mmr"],
        player2_new_mmr=rating_data["new_player2_mmr"]
    )

    matches_db[match_id] = updated_match
    return updated_match
from uuid import uuid4
from typing import List, Literal, Optional
import os

import httpx
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import Match

app = FastAPI(
    title="MATCHMAKING-UPV | Match Service",
    summary="Servicio de gestión de partidas",
    description="Crea partidas, las finaliza y actualiza MMR usando rating-service y player-service.",
    version="2.0.0",
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

    model_config = ConfigDict(from_attributes=True)


class MatchFinishRequest(BaseModel):
    winner_id: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "match-service"}


@app.post("/matches", tags=["matches"], response_model=MatchResponse, status_code=201)
def create_match(data: MatchCreate, db: Session = Depends(get_db)):
    if data.player1_id == data.player2_id:
        raise HTTPException(status_code=400, detail="Los jugadores deben ser diferentes")

    match = Match(
        id=str(uuid4()),
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

    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@app.get("/matches", tags=["matches"], response_model=List[MatchResponse])
def list_matches(db: Session = Depends(get_db)):
    return db.query(Match).all()


@app.get("/matches/{match_id}", tags=["matches"], response_model=MatchResponse)
def get_match(match_id: str, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return match


@app.patch("/matches/{match_id}/finish", tags=["matches"], response_model=MatchResponse)
def finish_match(match_id: str, data: MatchFinishRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == match_id).first()
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

        response1 = httpx.put(
            f"{PLAYER_SERVICE_URL}/players/{match.player1_id}/mmr",
            json={"mmr": rating_data["new_player1_mmr"]},
            timeout=10.0
        )
        response1.raise_for_status()

        response2 = httpx.put(
            f"{PLAYER_SERVICE_URL}/players/{match.player2_id}/mmr",
            json={"mmr": rating_data["new_player2_mmr"]},
            timeout=10.0
        )
        response2.raise_for_status()

    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="No se pudo conectar con rating-service o player-service")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error en servicio interno: {e.response.text}")

    match.status = "finished"
    match.winner_id = data.winner_id
    match.player1_new_mmr = rating_data["new_player1_mmr"]
    match.player2_new_mmr = rating_data["new_player2_mmr"]

    db.commit()
    db.refresh(match)
    return match
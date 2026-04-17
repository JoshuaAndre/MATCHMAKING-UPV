from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional
from uuid import uuid4

app = FastAPI(
    title="Match Service",
    description="Microservicio para gestión de partidas",
    version="1.0.0"
)


class MatchCreate(BaseModel):
    player1_id: str
    player2_id: str
    region: str = Field(default="mx")
    mode: str = Field(default="1v1")


class MatchResponse(BaseModel):
    id: str
    player1_id: str
    player2_id: str
    region: str
    mode: str
    status: Literal["pending", "finished"]
    winner_id: Optional[str] = None


class MatchFinishRequest(BaseModel):
    winner_id: str


matches_db: Dict[str, MatchResponse] = {}


@app.get("/health")
def health():
    return {"status": "ok", "service": "match-service"}


@app.post("/matches", response_model=MatchResponse, status_code=201)
def create_match(data: MatchCreate):
    if data.player1_id == data.player2_id:
        raise HTTPException(status_code=400, detail="Los jugadores deben ser diferentes")

    match_id = str(uuid4())
    match = MatchResponse(
        id=match_id,
        player1_id=data.player1_id,
        player2_id=data.player2_id,
        region=data.region,
        mode=data.mode,
        status="pending",
        winner_id=None
    )
    matches_db[match_id] = match
    return match


@app.get("/matches", response_model=List[MatchResponse])
def list_matches():
    return list(matches_db.values())


@app.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(match_id: str):
    match = matches_db.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return match


@app.patch("/matches/{match_id}/finish", response_model=MatchResponse)
def finish_match(match_id: str, data: MatchFinishRequest):
    match = matches_db.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    if match.status == "finished":
        raise HTTPException(status_code=400, detail="La partida ya fue finalizada")

    if data.winner_id not in [match.player1_id, match.player2_id]:
        raise HTTPException(status_code=400, detail="El ganador no pertenece a esta partida")

    updated_match = MatchResponse(
        id=match.id,
        player1_id=match.player1_id,
        player2_id=match.player2_id,
        region=match.region,
        mode=match.mode,
        status="finished",
        winner_id=data.winner_id
    )

    matches_db[match_id] = updated_match
    return updated_match

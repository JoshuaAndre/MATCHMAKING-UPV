from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import os

app = FastAPI(
    title="MATCHMAKING-UPV | Matchmaking Service",
    summary="Servicio de colas y emparejamiento",
    description="Gestiona la cola de jugadores y crea partidas automáticamente.",
    version="1.2.0",
    openapi_tags=[
        {"name": "health", "description": "Estado del servicio."},
        {"name": "queue", "description": "Gestión de la cola de jugadores."},
    ]
)

MATCH_SERVICE_URL = os.getenv("MATCH_SERVICE_URL", "http://match-service:8000")


class QueuePlayer(BaseModel):
    player_id: str = Field(..., examples=["p1"])
    username: str = Field(..., examples=["JoshuaPlayer"])
    mmr: int = Field(..., ge=0, examples=[1200])
    region: str = Field(default="mx", examples=["mx"])


class QueueResponse(BaseModel):
    message: str
    total_in_queue: int
    match_created: bool
    match_data: Optional[dict] = None


queue: List[dict] = []


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "matchmaking-service"}


@app.get("/queue", tags=["queue"])
def get_queue():
    return {"total": len(queue), "players": queue}


@app.post("/queue", tags=["queue"], response_model=QueueResponse)
def add_to_queue(player: QueuePlayer):
    for existing in queue:
        if existing["player_id"] == player.player_id:
            raise HTTPException(status_code=400, detail="El jugador ya está en la cola")

    queue.append(player.model_dump())

    if len(queue) < 2:
        return QueueResponse(
            message="Jugador agregado a la cola. Aún no hay suficientes jugadores para crear una partida.",
            total_in_queue=len(queue),
            match_created=False,
            match_data=None
        )

    player1 = queue.pop(0)
    player2 = queue.pop(0)

    try:
        response = httpx.post(
            f"{MATCH_SERVICE_URL}/matches",
            json={
                "player1_id": player1["player_id"],
                "player1_mmr": player1["mmr"],
                "player2_id": player2["player_id"],
                "player2_mmr": player2["mmr"],
                "region": player1["region"],
                "mode": "1v1"
            },
            timeout=10.0
        )
        response.raise_for_status()
        match_data = response.json()

        return QueueResponse(
            message="Partida creada correctamente desde matchmaking-service.",
            total_in_queue=len(queue),
            match_created=True,
            match_data=match_data
        )

    except httpx.RequestError:
        queue.insert(0, player2)
        queue.insert(0, player1)
        raise HTTPException(status_code=502, detail="No se pudo conectar con match-service")

    except httpx.HTTPStatusError as e:
        queue.insert(0, player2)
        queue.insert(0, player1)
        raise HTTPException(
            status_code=502,
            detail=f"match-service respondió con error: {e.response.text}"
        )
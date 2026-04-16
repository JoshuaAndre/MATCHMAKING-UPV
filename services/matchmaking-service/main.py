from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Matchmaking Service",
    description="Microservicio para gestión de colas y emparejamiento",
    version="1.0.0"
)

queue: List[dict] = []


class QueuePlayer(BaseModel):
    player_id: str
    username: str
    mmr: int
    region: str = "mx"


@app.get("/health")
def health():
    return {"status": "ok", "service": "matchmaking-service"}


@app.get("/queue")
def get_queue():
    return {"total": len(queue), "players": queue}


@app.post("/queue")
def add_to_queue(player: QueuePlayer):
    queue.append(player.model_dump())
    return {"message": "Jugador agregado a la cola", "player": player}
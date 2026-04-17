from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="MATCHMAKING-UPV | Rating Service",
    summary="Servicio de cálculo de MMR",
    description="Calcula nuevos valores de MMR usando una fórmula tipo Elo.",
    version="1.1.0",
    openapi_tags=[
        {"name": "health", "description": "Estado del servicio."},
        {"name": "rating", "description": "Cálculo de rating."},
    ]
)


class RatingRequest(BaseModel):
    player1_id: str
    player1_mmr: int = Field(..., ge=0)
    player2_id: str
    player2_mmr: int = Field(..., ge=0)
    winner_id: str
    k_factor: int = Field(default=32, gt=0)


class RatingResponse(BaseModel):
    player1_id: str
    old_player1_mmr: int
    new_player1_mmr: int
    player2_id: str
    old_player2_mmr: int
    new_player2_mmr: int
    winner_id: str


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "rating-service"}


def expected_score(player_mmr: int, opponent_mmr: int) -> float:
    return 1 / (1 + 10 ** ((opponent_mmr - player_mmr) / 400))


@app.post("/calculate", tags=["rating"], response_model=RatingResponse)
def calculate_rating(data: RatingRequest):
    player1_expected = expected_score(data.player1_mmr, data.player2_mmr)
    player2_expected = expected_score(data.player2_mmr, data.player1_mmr)

    player1_score = 1 if data.winner_id == data.player1_id else 0
    player2_score = 1 if data.winner_id == data.player2_id else 0

    new_player1_mmr = round(data.player1_mmr + data.k_factor * (player1_score - player1_expected))
    new_player2_mmr = round(data.player2_mmr + data.k_factor * (player2_score - player2_expected))

    return RatingResponse(
        player1_id=data.player1_id,
        old_player1_mmr=data.player1_mmr,
        new_player1_mmr=new_player1_mmr,
        player2_id=data.player2_id,
        old_player2_mmr=data.player2_mmr,
        new_player2_mmr=new_player2_mmr,
        winner_id=data.winner_id
    )
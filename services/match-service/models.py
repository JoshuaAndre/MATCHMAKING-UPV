from sqlalchemy import Column, String, Integer
from database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, index=True)
    player1_id = Column(String, nullable=False, index=True)
    player1_mmr = Column(Integer, nullable=False)
    player2_id = Column(String, nullable=False, index=True)
    player2_mmr = Column(Integer, nullable=False)
    region = Column(String, nullable=False, default="mx")
    mode = Column(String, nullable=False, default="1v1")
    status = Column(String, nullable=False, default="pending")
    winner_id = Column(String, nullable=True)
    player1_new_mmr = Column(Integer, nullable=True)
    player2_new_mmr = Column(Integer, nullable=True)

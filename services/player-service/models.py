from sqlalchemy import Column, String, Integer
from database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    mmr = Column(Integer, nullable=False, default=1000)
    region = Column(String, nullable=False, default="mx")

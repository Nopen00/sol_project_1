"""Oracle drone model specifications mapping (read only)."""
from sqlalchemy import Column, Float, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DroneModelSpec(Base):
    __tablename__ = "DRONE_MODEL_SPECS"
    __table_args__ = {"schema": "DRONE_APP"}

    MODEL_ID = Column(String, primary_key=True)
    MODEL_NAME = Column(String)
    EVALUATION_WIND_MS = Column(Float)
    MIN_OPERATING_TEMP_C = Column(Float)
    MAX_OPERATING_TEMP_C = Column(Float)

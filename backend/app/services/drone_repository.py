"""Drone database reads; response contracts retained."""
from sqlalchemy import select
from app.core.database import get_session
from app.models.drone import DroneModelSpec


def get_drones():
    with get_session() as session:
        rows = session.execute(select(DroneModelSpec).order_by(DroneModelSpec.MODEL_NAME)).scalars().all()
        return [{
            "id": row.MODEL_ID,
            "name": row.MODEL_NAME,
            "wind": float(row.EVALUATION_WIND_MS),
            "minTemp": float(row.MIN_OPERATING_TEMP_C),
            "maxTemp": float(row.MAX_OPERATING_TEMP_C),
        } for row in rows]


def get_drone(model_id):
    with get_session() as session:
        row = session.get(DroneModelSpec, model_id)
        if row is None:
            return None
        return {
            "id": row.MODEL_ID,
            "name": row.MODEL_NAME,
            "max_wind": float(row.EVALUATION_WIND_MS) if row.EVALUATION_WIND_MS is not None else None,
            "min_temp": float(row.MIN_OPERATING_TEMP_C) if row.MIN_OPERATING_TEMP_C is not None else None,
            "max_temp": float(row.MAX_OPERATING_TEMP_C) if row.MAX_OPERATING_TEMP_C is not None else None,
        }

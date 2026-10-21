import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv
from fastapi import APIRouter

# backend/.env 파일 불러오기
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

router = APIRouter()


@router.get("/drones")
def get_drones():
    with oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "11522")),
        service_name=os.getenv("DB_SERVICE"),
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    MODEL_ID,
                    MODEL_NAME,
                    EVALUATION_WIND_MS,
                    MIN_OPERATING_TEMP_C,
                    MAX_OPERATING_TEMP_C
                FROM DRONE_APP.DRONE_MODEL_SPECS
                ORDER BY MODEL_NAME
            """)

            drones = []

            for model_id, name, wind, min_temp, max_temp in cursor:
                drones.append({
                    "id": model_id,
                    "name": name,
                    "wind": float(wind),
                    "minTemp": float(min_temp),
                    "maxTemp": float(max_temp),
                })

            return drones
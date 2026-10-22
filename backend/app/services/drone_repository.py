import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv


# backend/.env 불러오기
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


def get_drone(model_id):
    with oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "11522")),
        service_name=os.getenv("DB_SERVICE"),
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    MODEL_ID,
                    MODEL_NAME,
                    EVALUATION_WIND_MS,
                    MIN_OPERATING_TEMP_C,
                    MAX_OPERATING_TEMP_C
                FROM DRONE_APP.DRONE_MODEL_SPECS
                WHERE MODEL_ID = :model_id
                """,
                {"model_id": model_id},
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "id": row[0],
                "name": row[1],
                "max_wind": float(row[2]) if row[2] is not None else None,
                "min_temp": float(row[3]) if row[3] is not None else None,
                "max_temp": float(row[4]) if row[4] is not None else None,
            }


if __name__ == "__main__":
    drone = get_drone("AUTEL_EVO_LITE")

    if drone is None:
        print("해당 드론을 찾을 수 없습니다.")
    else:
        print("=== 드론 DB 조회 성공 ===")
        print(drone)
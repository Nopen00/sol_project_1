import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv

# backend/.env 읽기
load_dotenv(Path(__file__).resolve().parent / ".env")

# Oracle DB 연결
with oracledb.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "11522")),
    service_name=os.getenv("DB_SERVICE"),
) as connection:

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT MODEL_NAME, EVALUATION_WIND_MS
            FROM DRONE_APP.DRONE_MODEL_SPECS
            ORDER BY MODEL_NAME
        """)

        for name, wind in cursor:
            print(f"{name}: {wind} m/s")
import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv

# backend/.env 파일 불러오기
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)


def get_weather(nx, ny):
    # Oracle DB 연결
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
                    FORECAST_AT,
                    TEMPERATURE_C,
                    WIND_SPEED_MS,
                    PTY_RAW,
                    PCP_RAW,
                    PTY_STATUS,
                    PCP_STATUS
                FROM DRONE_APP.WEATHER_NATIONAL_FORECAST_V2
                WHERE NX = :nx
                  AND NY = :ny
                  AND FORECAST_AT >= CURRENT_TIMESTAMP
                ORDER BY FORECAST_AT ASC
                FETCH FIRST 1 ROW ONLY
                """,
                {"nx": nx, "ny": ny},
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "forecast_at": row[0],
                "temperature": row[1],
                "wind_speed": row[2],
                "pty_raw": row[3],
                "pcp_raw": row[4],
                "pty_status": row[5],
                "pcp_status": row[6],
            }

if __name__ == "__main__":
    from weather_suitability import evaluate_wind, evaluate_temperature

    weather = get_weather(60, 127)

    if weather is None:
        print("조회 가능한 미래 날씨 데이터가 없습니다.")
    else:
        print("=== 실제 날씨 평가 ===")

        # 임시 드론 사양 (테스트용)
        max_wind = 8.0
        min_temp = -10
        max_temp = 40

        wind_result = evaluate_wind(
            weather["wind_speed"],
            max_wind
        )

        temp_result = evaluate_temperature(
            weather["temperature"],
            min_temp,
            max_temp
        )

        print("예보 시간:", weather["forecast_at"])
        print("풍속 평가:", wind_result)
        print("기온 평가:", temp_result)
        print("강수 데이터 상태:", weather["pty_status"], weather["pcp_status"])
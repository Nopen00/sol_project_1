
from datetime import date, datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from backend.app.services.weather_forecast import load_env
from backend.app.services.weather_grid import latlon_to_grid


def get_weather(day: str, latitude: float, longitude: float):
    # 1. 날짜와 위도·경도를 기상청 격자로 변환
    target_date = date.fromisoformat(day)
    nx, ny = latlon_to_grid(latitude, longitude)

    print(f"조회 날짜: {target_date}")
    print(f"기상청 격자: NX={nx}, NY={ny}")

    # 2. Oracle DB 연결 정보
    env = load_env()

    if (
        env.get("DB_HOST") not in ("localhost", "127.0.0.1")
        or env.get("DB_USER", "").upper() != "DRONE_APP"
    ):
        raise RuntimeError("로컬 실습 DB가 아닙니다.")

    db_url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={"service_name": env["DB_SERVICE"]},
    )

    # 3. 날짜와 격자에 맞는 날씨 검색
    query = text("""
        SELECT
            NX,
            NY,
            FORECAST_AT,
            ISSUED_AT,
            TEMPERATURE_C,
            WIND_SPEED_MS,
            WIND_DIRECTION_DEG
        FROM WEATHER_NATIONAL_FORECAST_PRACTICE
        WHERE SOURCE_API = 'nph-dfs_shrt_grd'
          AND NX = :nx
          AND NY = :ny
          AND FORECAST_AT >= :start_at
          AND FORECAST_AT < :end_at
        ORDER BY FORECAST_AT
    """)

    start_at = datetime.combine(
        target_date, datetime.min.time()
    )
    end_at = start_at + timedelta(days=1)

    # 4. DB에서 조회한 결과 반환
    engine = create_engine(db_url)

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                query,
                {
                    "nx": nx,
                    "ny": ny,
                    "start_at": start_at,
                    "end_at": end_at,
                },
            ).mappings().all()

            return [dict(row) for row in rows]

    finally:
        engine.dispose()


if __name__ == "__main__":
    # 서울시청 좌표로 테스트
    results = get_weather(
        day="2026-10-15",
        latitude=37.5665,
        longitude=126.9780,
    )

    print("\n===== 서울 날씨 조회 결과 =====")
    print("조회 건수:", len(results))

   
    for row in results:
        print(
            "예보 시각:", row["forecast_at"],
            "| 기온:", row["temperature_c"], "°C",
            "| 풍속:", row["wind_speed_ms"], "m/s",
            "| 풍향:", row["wind_direction_deg"], "°",
        )


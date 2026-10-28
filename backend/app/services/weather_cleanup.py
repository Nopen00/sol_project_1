
import sys
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from backend.app.services.weather_forecast import KST, load_env


def main():
    env = load_env()

    # 로컬 실습 DB만 허용
    if env.get("DB_HOST") not in ("localhost", "127.0.0.1"):
        raise SystemExit("로컬 실습 DB가 아닙니다.")

    if env.get("DB_USER", "").upper() != "DRONE_APP":
        raise SystemExit("실습용 DB 계정이 아닙니다.")

    options = sys.argv[1:]

    if options not in ([], ["--delete-old"]):
        raise SystemExit("지원하지 않는 실행 옵션입니다.")

    delete_mode = options == ["--delete-old"]

    # 한국시간 기준 24시간 전
    now = datetime.now(KST).replace(tzinfo=None)
    cutoff = now - timedelta(hours=24)

    db_url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={"service_name": env["DB_SERVICE"]},
    )

    engine = create_engine(db_url)

    # 1. 오래된 실황 데이터 조회
    observation_sql = text("""
        SELECT ID, BASE_DATE, BASE_TIME
        FROM WEATHER_PRACTICE
        WHERE TO_DATE(
            BASE_DATE || BASE_TIME,
            'YYYYMMDDHH24MI'
        ) <= :cutoff
        ORDER BY ID
    """)

    # 2. 오래된 미래 예보 조회
    forecast_sql = text("""
        SELECT ID, FORECAST_AT, ISSUED_AT
        FROM WEATHER_FORECAST_PRACTICE
        WHERE FORECAST_AT <= :cutoff
        ORDER BY FORECAST_AT
    """)

    # 3. 기존 실황 삭제 기능
    delete_observation_sql = text("""
        DELETE FROM WEATHER_PRACTICE
        WHERE TO_DATE(
            BASE_DATE || BASE_TIME,
            'YYYYMMDDHH24MI'
        ) <= :cutoff
    """)

    try:
        with engine.begin() as conn:

            observations = conn.execute(
                observation_sql,
                {"cutoff": cutoff}
            ).all()

            forecasts = conn.execute(
                forecast_sql,
                {"cutoff": cutoff}
            ).all()

            print("현재 한국시간:", now)
            print("삭제 기준 시각:", cutoff)
            print()

            print("=== 실황 데이터 ===")
            print("삭제 대상:", len(observations), "건")

            for row in observations[:10]:
                print("실황:", row[0], row[1], row[2])

            print()
            print("=== 미래 예보 데이터 ===")
            print("삭제 대상:", len(forecasts), "건")

            for row in forecasts[:10]:
                print("예보:", row[0], row[1], row[2])

            if delete_mode:
                result = conn.execute(
                    delete_observation_sql,
                    {"cutoff": cutoff}
                )

                print()
                print("실황 실제 삭제:", result.rowcount, "건")
                print("미래 예보는 아직 삭제하지 않았습니다.")
            else:
                print()
                print("안전 모드: 실제 삭제하지 않았습니다.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

"""오래된 날씨 데이터 정리. 기본 실행은 조회만 수행."""

import argparse

from sqlalchemy import text

from backend.app.services.weather_forecast import load_env
from backend.app.services.weather_national_v2_collect import engine_for


TABLES = (
    ("WEATHER_NATIONAL_FORECAST_V2", "FORECAST_AT"),
    ("WEATHER_CURRENT_OBS_V2", "OBSERVED_AT"),
)

CUTOFF_SQL = text("""
    SELECT CAST(
        SYSTIMESTAMP AT TIME ZONE '+09:00'
        AS TIMESTAMP
    ) - NUMTODSINTERVAL(48, 'HOUR')
    FROM DUAL
""")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제 삭제 실행. 생략하면 건수만 확인",
    )
    args = parser.parse_args()

    engine = engine_for(load_env())

    try:
        with engine.begin() as conn:
            cutoff = conn.execute(CUTOFF_SQL).scalar_one()

            print("DB 기준 삭제 시각:", cutoff)
            print("실제 삭제:", args.apply)

            for table, column in TABLES:
                where = f"{column} < :cutoff"

                count = conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {table} "
                        f"WHERE {where}"
                    ),
                    {"cutoff": cutoff},
                ).scalar_one()

                print(f"{table}: 삭제 대상 {count:,}행")

                if args.apply:
                    result = conn.execute(
                        text(
                            f"DELETE FROM {table} "
                            f"WHERE {where}"
                        ),
                        {"cutoff": cutoff},
                    )
                    print(
                        f"{table}: 실제 삭제 "
                        f"{result.rowcount:,}행"
                    )

        print("작업 완료")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

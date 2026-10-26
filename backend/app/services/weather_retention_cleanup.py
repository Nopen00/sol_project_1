"""48시간이 지난 날씨 데이터를 안전하게 배치 삭제."""

import argparse

from sqlalchemy import text

from backend.app.services.weather_forecast import load_env
from backend.app.services.weather_national_v2_collect import engine_for


TABLES = (
    ("WEATHER_NATIONAL_FORECAST_V2", "FORECAST_AT"),
    ("WEATHER_CURRENT_OBS_V2", "OBSERVED_AT"),
)

BATCH_SIZE = 5000

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
        help="실제 삭제 실행. 기본값은 조회만 수행",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="테스트용 최대 삭제 배치 수",
    )
    args = parser.parse_args()

    if args.max_batches is not None and args.max_batches < 1:
        parser.error("--max-batches는 1 이상이어야 합니다.")

    engine = engine_for(load_env())
    completed_batches = 0

    try:
        with engine.connect() as conn:
            cutoff = conn.execute(CUTOFF_SQL).scalar_one()

        print("DB 기준 삭제 시각:", cutoff)
        print("실제 삭제:", args.apply)
        print("배치 크기:", BATCH_SIZE)

        for table, column in TABLES:
            with engine.connect() as conn:
                count = conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {table} "
                        f"WHERE {column} < :cutoff"
                    ),
                    {"cutoff": cutoff},
                ).scalar_one()

            print(f"{table}: 삭제 대상 {count:,}행")

            if not args.apply:
                continue

            delete_sql = text(f"""
                DELETE FROM {table}
                WHERE ROWID IN (
                    SELECT ROWID
                    FROM {table}
                    WHERE {column} < :cutoff
                      AND ROWNUM <= :batch_size
                )
            """)

            total_deleted = 0
            table_batches = 0

            while True:
                with engine.begin() as conn:
                    result = conn.execute(
                        delete_sql,
                        {
                            "cutoff": cutoff,
                            "batch_size": BATCH_SIZE,
                        },
                    )
                    deleted = result.rowcount

                if deleted < 0:
                    raise RuntimeError("삭제 건수를 확인할 수 없습니다.")

                if deleted == 0:
                    break

                total_deleted += deleted
                table_batches += 1
                completed_batches += 1

                if table_batches % 5 == 0 or deleted < BATCH_SIZE:
                    print(
                        f"{table}: 누적 삭제 "
                        f"{total_deleted:,}행 / "
                        f"{table_batches}배치",
                        flush=True,
                    )

                if (
                    args.max_batches is not None
                    and completed_batches >= args.max_batches
                ):
                    print(
                        f"테스트 제한 도달: "
                        f"총 {completed_batches}배치 완료"
                    )
                    return

            print(
                f"{table}: 실제 삭제 완료 "
                f"{total_deleted:,}행"
            )

        print("작업 완료")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

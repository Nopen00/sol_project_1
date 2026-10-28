
import argparse
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from backend.app.services.weather_forecast import (
    KST,
    get_base_datetime,
    load_env,
)

from backend.app.services.weather_national_save import (
    fetch_grid,
    get_value,
    MERGE_SQL,
)


TOTAL_X = 149
TOTAL_Y = 253
BATCH_SIZE = 500


def main():
    # 1. 실행 옵션 설정
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--save",
        action="store_true",
        help="전국 날씨 데이터를 Oracle에 실제 저장",
    )

    parser.add_argument(
        "--forecast-at",
        help="조회할 예보 시각 (예: 2026-10-16T12:00)",
    )

    args = parser.parse_args()

    # 2. 환경변수 및 DB 접속 정보 확인
    env = load_env()

    if env.get("DB_HOST") not in ("localhost", "127.0.0.1"):
        raise SystemExit("중단: 로컬 실습 DB가 아닙니다.")

    if env.get("DB_USER", "").upper() != "DRONE_APP":
        raise SystemExit("중단: 실습용 DB 계정이 아닙니다.")

    key = env.get("KMA_HUB_KEY", "")

    if not key:
        raise SystemExit("API허브 인증키가 없습니다.")

    # 3. 발표 시각과 예보 시각 설정
    now = datetime.now(KST)

    # 수정: 현재 시점 기준 이용 가능한 최신 발표 시각 선택
    base = get_base_datetime(now + timedelta(minutes=40))

    # 기본 예보 시각
    forecast_time = (
        now + timedelta(hours=4)
    ).replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    # 사용자가 예보 시각을 지정했다면 해당 시각 사용
    if args.forecast_at:
        try:
            forecast_time = datetime.strptime(
                args.forecast_at,
                "%Y-%m-%dT%H:%M",
            ).replace(tzinfo=KST)

        except ValueError:
            raise SystemExit(
                "예보 시각 형식 오류: "
                "YYYY-MM-DDTHH:MM 형식으로 입력하세요."
            ) from None

    print("발표 시각:", base)
    print("예보 시각:", forecast_time)

    # 4. 기상청 전국 날씨 데이터 수집
    grids = {}

    for category in ("TMP", "WSD", "VEC"):
        print(f"{category} 전국 자료 수집 중...")

        try:
            grids[category] = fetch_grid(
                key,
                base,
                forecast_time,
                category,
            )

        except Exception as exc:
            reason = (
                str(exc)
                if isinstance(exc, RuntimeError)
                else type(exc).__name__
            )

            raise SystemExit(
                f"{category} 수집 실패: "
                f"{reason}. DB 저장 중단."
            ) from None

    # 5. 전국 격자별 데이터 결합
    records = []

    for ny in range(1, TOTAL_Y + 1):
        for nx in range(1, TOTAL_X + 1):

            temperature = get_value(
                grids["TMP"], nx, ny
            )

            wind_speed = get_value(
                grids["WSD"], nx, ny
            )

            wind_direction = get_value(
                grids["VEC"], nx, ny
            )

            # 세 항목이 모두 없으면 저장하지 않음
            if all(
                value is None
                for value in (
                    temperature,
                    wind_speed,
                    wind_direction,
                )
            ):
                continue

            records.append({
                "source_api": "nph-dfs_shrt_grd",
                "nx": nx,
                "ny": ny,
                "forecast_at": forecast_time.replace(
                    tzinfo=None
                ),
                "issued_at": base.replace(
                    tzinfo=None
                ),
                "temperature_c": temperature,
                "wind_speed_ms": wind_speed,
                "wind_direction_deg": wind_direction,
            })

    # 6. 데이터 분석
    print("\n===== 전국 데이터 분석 =====")
    print("전체 격자:", TOTAL_X * TOTAL_Y)
    print("저장 대상 격자:", len(records))

    complete_count = sum(
        1
        for record in records
        if all(
            record[field] is not None
            for field in (
                "temperature_c",
                "wind_speed_ms",
                "wind_direction_deg",
            )
        )
    )

    print("세 항목 모두 있는 격자:", complete_count)

    # 7. 저장 옵션이 없으면 미리보기만 진행
    if not args.save:
        print("\n미리보기 완료!")
        print("Oracle DB는 수정하지 않았습니다.")
        print("실제 저장은 --save 옵션으로 실행합니다.")
        return

    # 8. Oracle DB 연결
    db_url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={
            "service_name": env["DB_SERVICE"]
        },
    )

    engine = create_engine(db_url)

    try:
        with engine.begin() as conn:
            changed = 0

            # 9. 500건씩 MERGE 처리
            for start in range(
                0,
                len(records),
                BATCH_SIZE,
            ):
                batch = records[
                    start:start + BATCH_SIZE
                ]

                result = conn.execute(
                    MERGE_SQL,
                    batch,
                )

                if result.rowcount >= 0:
                    changed += result.rowcount

                print(
                    f"처리 중: "
                    f"{min(start + BATCH_SIZE, len(records))}"
                    f" / {len(records)}"
                )

            # 10. DB 저장 건수 확인
            total = conn.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM WEATHER_NATIONAL_FORECAST_PRACTICE"
                )
            ).scalar_one()

        print("\n===== Oracle 저장 결과 =====")
        print("변경된 행:", changed)
        print("테이블 전체 행:", total)
        print("전국 날씨 저장 완료!")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

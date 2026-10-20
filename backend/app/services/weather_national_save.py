
import re
from datetime import datetime, timedelta
from urllib.parse import unquote

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from backend.app.services.weather_forecast import (
    KST,
    get_base_datetime,
    load_env,
)


API_URL = (
    "https://apihub.kma.go.kr/api/typ01/cgi-bin/url/"
    "nph-dfs_shrt_grd"
)

LOCATIONS = {
    "서울": (60, 127),
    "부산": (98, 76),
    "제주": (53, 38),
}

MERGE_SQL = text("""
MERGE INTO WEATHER_NATIONAL_FORECAST_PRACTICE t
USING (
    SELECT
        :source_api AS source_api,
        :nx AS nx,
        :ny AS ny,
        :forecast_at AS forecast_at
    FROM DUAL
) s
ON (
    t.SOURCE_API = s.source_api
    AND t.NX = s.nx
    AND t.NY = s.ny
    AND t.FORECAST_AT = s.forecast_at
)
WHEN MATCHED THEN UPDATE SET
    t.ISSUED_AT = :issued_at,
    t.TEMPERATURE_C = :temperature_c,
    t.WIND_SPEED_MS = :wind_speed_ms,
    t.WIND_DIRECTION_DEG = :wind_direction_deg,
    t.FETCHED_AT = CURRENT_TIMESTAMP
WHERE
    t.ISSUED_AT <= :issued_at
    AND (
        DECODE(t.TEMPERATURE_C, :temperature_c, 1, 0) = 0
        OR DECODE(t.WIND_SPEED_MS, :wind_speed_ms, 1, 0) = 0
        OR DECODE(t.WIND_DIRECTION_DEG, :wind_direction_deg, 1, 0) = 0
    )
WHEN NOT MATCHED THEN INSERT (
    SOURCE_API,
    NX,
    NY,
    FORECAST_AT,
    ISSUED_AT,
    TEMPERATURE_C,
    WIND_SPEED_MS,
    WIND_DIRECTION_DEG
)
VALUES (
    :source_api,
    :nx,
    :ny,
    :forecast_at,
    :issued_at,
    :temperature_c,
    :wind_speed_ms,
    :wind_direction_deg
)
""")



def fetch_grid(key, base, forecast_time, category):
    import time

    for attempt in range(1, 4):
        print(f"{category} API 요청: {attempt}/3회")

        try:
            response = requests.get(
                API_URL,
                params={
                    "tmfc": base.strftime("%Y%m%d%H"),
                    "tmef": forecast_time.strftime("%Y%m%d%H"),
                    "vars": category,
                    "authKey": unquote(key),
                },
                timeout=60,
            )

        except requests.RequestException:
            if attempt == 3:
                raise RuntimeError(
                    f"{category} API 연결 3회 실패"
                ) from None

            print("연결 오류: 잠시 후 재시도")
            time.sleep(3 * attempt)
            continue

        # 일시적인 서버 오류는 자동 재시도
        if response.status_code in (429, 500, 502, 503, 504):
            if attempt == 3:
                raise RuntimeError(
                    f"{category} HTTP {response.status_code}: "
                    "3회 시도 후 중단"
                )

            print(
                f"HTTP {response.status_code}: "
                "잠시 후 자동 재시도"
            )
            time.sleep(3 * attempt)
            continue

        if response.status_code != 200:
            raise RuntimeError(
                f"{category} API 응답 실패: "
                f"HTTP {response.status_code}"
            )

        numbers = [
            float(value)
            for value in re.findall(
                r"-?\d+(?:\.\d+)?",
                response.text,
            )
        ]

        if len(numbers) != 149 * 253:
            raise RuntimeError(
                f"{category} 격자 개수 오류: "
                f"{len(numbers)}개. "
                "발표 및 예보 시각 확인 필요"
            )

        return numbers


    if response.status_code != 200:
        raise RuntimeError(
            f"{category} API 응답 실패: HTTP {response.status_code}"
        )

    numbers = [
        float(value)
        for value in re.findall(
            r"-?\d+(?:\.\d+)?",
            response.text,
        )
    ]

    if len(numbers) != 149 * 253:
        raise RuntimeError(
            f"{category} 격자 개수가 올바르지 않습니다."
        )

    return numbers


def get_value(grid, nx, ny):
    index = (ny - 1) * 149 + (nx - 1)
    value = grid[index]

    return None if value <= -99 else value


def main():
    env = load_env()

    # 기존 로컬 실습 DB에서만 실행
    if env.get("DB_HOST") not in ("localhost", "127.0.0.1"):
        print("중단: 로컬 실습 DB가 아닙니다.")
        return

    if env.get("DB_USER", "").upper() != "DRONE_APP":
        print("중단: 실습용 DRONE_APP 계정이 아닙니다.")
        return

    key = env.get("KMA_HUB_KEY", "")

    if not key:
        print("중단: API허브 인증키가 없습니다.")
        return

    now = datetime.now(KST)
    base = get_base_datetime(now - timedelta(hours=3))
    forecast_time = (
        now + timedelta(hours=4)
    ).replace(minute=0, second=0, microsecond=0)

    print("발표 시각:", base.strftime("%Y-%m-%d %H:%M"))
    print("예보 시각:", forecast_time.strftime("%Y-%m-%d %H:%M"))

    # 세 자료를 모두 받은 다음 저장 시작
    grids = {}

    try:
        for category in ("TMP", "WSD", "VEC"):
            print(f"{category} 전국 자료 수집 중...")
            grids[category] = fetch_grid(
                key, base, forecast_time, category
            )
    except (requests.RequestException, RuntimeError) as exc:
        print("수집 중단:", str(exc))
        print("Oracle DB는 변경하지 않았습니다.")
        return

    db_url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={"service_name": env["DB_SERVICE"]},
    )

    engine = create_engine(db_url)

    try:
        with engine.begin() as conn:
            changed = 0

            for name, (nx, ny) in LOCATIONS.items():
                record = {
                    "source_api": "nph-dfs_shrt_grd",
                    "nx": nx,
                    "ny": ny,
                    "forecast_at": forecast_time.replace(
                        tzinfo=None
                    ),
                    "issued_at": base.replace(tzinfo=None),
                    "temperature_c": get_value(
                        grids["TMP"], nx, ny
                    ),
                    "wind_speed_ms": get_value(
                        grids["WSD"], nx, ny
                    ),
                    "wind_direction_deg": get_value(
                        grids["VEC"], nx, ny
                    ),
                }

                changed += conn.execute(
                    MERGE_SQL, record
                ).rowcount

                print(
                    f"{name} 저장 처리:",
                    f"기온={record['temperature_c']},",
                    f"풍속={record['wind_speed_ms']},",
                    f"풍향={record['wind_direction_deg']}",
                )

            total = conn.execute(text(
                "SELECT COUNT(*) "
                "FROM WEATHER_NATIONAL_FORECAST_PRACTICE"
            )).scalar_one()

        print("\n===== Oracle 저장 결과 =====")
        print("변경된 행:", changed)
        print("테이블 전체 행:", total)
        print("저장 작업 정상 완료!")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

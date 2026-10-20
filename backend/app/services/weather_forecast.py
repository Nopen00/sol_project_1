from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError


KST = timezone(timedelta(hours=9))

API_URL = (
    "https://apis.data.go.kr/1360000/"
    "VilageFcstInfoService_2.0/getVilageFcst"
)


def load_env():
    env_path = Path(__file__).resolve().parents[2] / ".env"
    env = {}

    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")

    return env


def get_base_datetime(now):
    safe = now - timedelta(minutes=40)
    hours = [2, 5, 8, 11, 14, 17, 20, 23]
    valid = [hour for hour in hours if hour <= safe.hour]

    if valid:
        return safe.replace(
            hour=valid[-1], minute=0, second=0, microsecond=0
        )

    return (safe - timedelta(days=1)).replace(
        hour=23, minute=0, second=0, microsecond=0
    )


def fetch_forecast(key, base, now):
    params = {
        "serviceKey": unquote(key),
        "pageNo": 1,
        "numOfRows": 2000,
        "dataType": "JSON",
        "base_date": base.strftime("%Y%m%d"),
        "base_time": base.strftime("%H%M"),
        "nx": 60,
        "ny": 127,
    }

    try:
        response = requests.get(API_URL, params=params, timeout=20)
        data = response.json()
    except (requests.RequestException, ValueError):
        # requests 예외 전체를 출력하면 인증키가 URL에 노출될 수 있음
        raise RuntimeError("기상청 API 연결 또는 응답 처리 실패") from None

    result = data.get("response", {})
    header = result.get("header", {})

    # 자료가 없는 경우에만 이전 발표 시각으로 재시도하도록 구분
    if response.status_code == 200 and header.get("resultCode") == "03":
        raise RuntimeError("NO_DATA")

    if response.status_code != 200 or header.get("resultCode") != "00":
        raise RuntimeError("기상청 API가 정상 응답하지 않았습니다.")

    body = result.get("body", {})
    items = body.get("items", {}).get("item", [])

    if not items:
        raise RuntimeError("기상청 예보 데이터가 없습니다.")

    if int(body.get("totalCount", 0)) > len(items):
        raise RuntimeError("예보 데이터가 여러 페이지로 나뉘어 있습니다.")

    forecast = {}
    current = now.strftime("%Y%m%d%H%M")

    for item in items:
        date = item["fcstDate"]
        time = item["fcstTime"]

        if date + time <= current:
            continue

        if not time.endswith("00") or int(time[:2]) % 3 != 0:
            continue

        slot = (date, time)
        forecast.setdefault(slot, {})[item["category"]] = item["fcstValue"]

    return forecast


def fetch_latest_available_forecast(key, now, max_attempts=8):
    """최신 발표부터 3시간씩 거슬러 올라가며 정상 자료를 찾는다."""
    base = get_base_datetime(now)

    for _ in range(max_attempts):
        try:
            forecast = fetch_forecast(key, base, now)
            if not forecast:
                raise RuntimeError("미래 시각의 예보 데이터가 없습니다.")
            return forecast, base
        except RuntimeError as exc:
            # 인증/네트워크 오류는 NO_DATA와 다르므로 무작정 재시도하지 않음
            if str(exc) != "NO_DATA":
                raise
            print("자료 없음:", base.strftime("%Y-%m-%d %H:%M"), "→ 이전 발표 확인")
            base -= timedelta(hours=3)

    raise RuntimeError("최근 8회 발표 자료 모두 NO_DATA: 기존 DB 데이터를 유지합니다.")


def numeric(value):
    if value is None:
        return None

    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


MERGE_SQL = text("""
MERGE INTO WEATHER_FORECAST_PRACTICE t
USING (
    SELECT :source_api AS source_api,
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
    t.TEMPERATURE_C = COALESCE(:temperature_c, t.TEMPERATURE_C),
    t.WIND_SPEED_MS = COALESCE(:wind_speed_ms, t.WIND_SPEED_MS),
    t.WIND_DIRECTION_DEG = COALESCE(:wind_direction_deg, t.WIND_DIRECTION_DEG),
    t.RAINFALL_RAW = COALESCE(:rainfall_raw, t.RAINFALL_RAW),
    t.RAIN_PROBABILITY_PCT = COALESCE(:rain_probability_pct, t.RAIN_PROBABILITY_PCT),
    t.SKY_CODE = COALESCE(:sky_code, t.SKY_CODE),
    t.PTY_CODE = COALESCE(:pty_code, t.PTY_CODE),
    t.FETCHED_AT = CURRENT_TIMESTAMP
    WHERE t.ISSUED_AT < :issued_at
WHEN NOT MATCHED THEN INSERT (
    SOURCE_API, NX, NY, FORECAST_AT, ISSUED_AT,
    TEMPERATURE_C, WIND_SPEED_MS, WIND_DIRECTION_DEG,
    RAINFALL_RAW, RAIN_PROBABILITY_PCT, SKY_CODE, PTY_CODE
) VALUES (
    :source_api, :nx, :ny, :forecast_at, :issued_at,
    :temperature_c, :wind_speed_ms, :wind_direction_deg,
    :rainfall_raw, :rain_probability_pct, :sky_code, :pty_code
)
""")


def save_forecast(env, forecast, base):
    db_url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={"service_name": env["DB_SERVICE"]},
    )

    engine = create_engine(db_url)
    changed = 0

    try:
        with engine.begin() as conn:
            for (date, time), values in sorted(forecast.items()):
                record = {
                    "source_api": "getVilageFcst",
                    "nx": 60,
                    "ny": 127,
                    "forecast_at": datetime.strptime(
                        date + time, "%Y%m%d%H%M"
                    ),
                    "issued_at": base.replace(tzinfo=None),
                    "temperature_c": numeric(values.get("TMP")),
                    "wind_speed_ms": numeric(values.get("WSD")),
                    "wind_direction_deg": numeric(values.get("VEC")),
                    "rainfall_raw": values.get("PCP"),
                    "rain_probability_pct": numeric(values.get("POP")),
                    "sky_code": values.get("SKY"),
                    "pty_code": values.get("PTY"),
                }

                result = conn.execute(MERGE_SQL, record)
                changed += result.rowcount

            total = conn.execute(text("""
                SELECT COUNT(*)
                FROM WEATHER_FORECAST_PRACTICE
            """)).scalar_one()

    finally:
        engine.dispose()

    return changed, total


def main():
    env = load_env()

    if env.get("DB_HOST") not in ("localhost", "127.0.0.1"):
        raise SystemExit("로컬 실습 DB가 아니므로 중단합니다.")

    if env.get("DB_USER", "").upper() != "DRONE_APP":
        raise SystemExit("실습용 DRONE_APP 계정이 아닙니다.")

    key = env.get("KMA_SERVICE_KEY", "")
    if not key:
        raise SystemExit("기상청 인증키가 없습니다.")

    now = datetime.now(KST)

    try:
        forecast, base = fetch_latest_available_forecast(key, now)
        changed, total = save_forecast(env, forecast, base)
    except RuntimeError as exc:
        raise SystemExit("작업 실패: " + str(exc)) from None
    except SQLAlchemyError:
        raise SystemExit("작업 실패: Oracle DB 저장 오류") from None

    print("실제 사용한 기상청 발표시각:", base.strftime("%Y-%m-%d %H:%M"))
    print("수집한 예보 시각:", len(forecast), "개")
    print("이번에 추가 또는 갱신:", changed, "개")
    print("Oracle 총 데이터:", total, "개")
    if now - base > timedelta(hours=6):
        print("주의: 발표 후 6시간이 지난 자료입니다. 화면에서 발표시각을 확인하세요.")
    print("날씨 예보 저장 성공!")


def get_saved_forecasts(nx: int, ny: int, limit: int = 20):
    """Oracle에 저장된 미래 날씨 예보 조회"""

    env = load_env()

    # 개인 실습용 Oracle DB만 허용
    if env.get("DB_HOST") not in ("localhost", "127.0.0.1"):
        raise RuntimeError("로컬 실습 DB가 아닙니다.")

    if env.get("DB_USER", "").upper() != "DRONE_APP":
        raise RuntimeError("실습용 계정이 아닙니다.")

    db_url = URL.create(
        "oracle+oracledb",
        username=env["DB_USER"],
        password=env["DB_PASSWORD"],
        host=env["DB_HOST"],
        port=int(env["DB_PORT"]),
        query={"service_name": env["DB_SERVICE"]},
    )

    engine = create_engine(db_url)

    # 현재 한국시간 기준 미래 데이터만 조회
    now = datetime.now(KST).replace(tzinfo=None)

    query = text("""
        SELECT *
        FROM (
            SELECT
                NX,
                NY,
                FORECAST_AT,
                ISSUED_AT,
                TEMPERATURE_C,
                WIND_SPEED_MS,
                WIND_DIRECTION_DEG,
                RAINFALL_RAW,
                RAIN_PROBABILITY_PCT,
                SKY_CODE,
                PTY_CODE
            FROM WEATHER_FORECAST_PRACTICE
            WHERE NX = :nx
              AND NY = :ny
              AND FORECAST_AT > :now
            ORDER BY FORECAST_AT ASC
        )
        WHERE ROWNUM <= :limit
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "nx": nx,
                    "ny": ny,
                    "now": now,
                    "limit": limit,
                },
            )

            rows = [dict(row) for row in result.mappings().all()]

        return rows

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

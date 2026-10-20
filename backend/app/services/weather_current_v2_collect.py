
"""기상청 초단기실황 조회 및 Oracle V2 저장."""

import argparse
import math
from datetime import datetime, timedelta
from urllib.parse import unquote

import requests
from sqlalchemy import text

from backend.app.services.weather_forecast import KST, load_env
from backend.app.services.weather_national_v2_collect import engine_for


API_URL = (
    "https://apis.data.go.kr/1360000/"
    "VilageFcstInfoService_2.0/getUltraSrtNcst"
)

SAVE_SQL = text("""
MERGE INTO WEATHER_CURRENT_OBS_V2 t
USING (
    SELECT :source_api AS source_api,
           :nx AS nx,
           :ny AS ny,
           :observed_at AS observed_at
    FROM DUAL
) s
ON (
    t.SOURCE_API = s.source_api
    AND t.NX = s.nx
    AND t.NY = s.ny
    AND t.OBSERVED_AT = s.observed_at
)
WHEN MATCHED THEN UPDATE SET
    t.RETRIEVED_AT = LOCALTIMESTAMP,
    t.TEMPERATURE_C = :temperature_c,
    t.WIND_SPEED_MS = :wind_speed_ms,
    t.WIND_DIRECTION_DEG = :wind_direction_deg,
    t.PTY_RAW = :pty_raw,
    t.RN1_RAW = :rn1_raw,
    t.RN1_AMOUNT_MM = :rn1_amount_mm,
    t.PTY_STATUS = :pty_status,
    t.RN1_STATUS = :rn1_status,
    t.DATA_QUALITY_FLAGS = :data_quality_flags
WHEN NOT MATCHED THEN INSERT (
    SOURCE_API, NX, NY, OBSERVED_AT,
    TEMPERATURE_C, WIND_SPEED_MS,
    WIND_DIRECTION_DEG, PTY_RAW, RN1_RAW,
    RN1_AMOUNT_MM, PTY_STATUS,
    RN1_STATUS, DATA_QUALITY_FLAGS
) VALUES (
    :source_api, :nx, :ny, :observed_at,
    :temperature_c, :wind_speed_ms,
    :wind_direction_deg, :pty_raw, :rn1_raw,
    :rn1_amount_mm, :pty_status,
    :rn1_status, :data_quality_flags
)
""")


def numeric(value):
    try:
        number = float(value)
        if math.isfinite(number) and number != -99:
            return number
    except (TypeError, ValueError, OverflowError):
        pass
    return None


def raw_value(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value and value != "-99" else None


def fetch_latest_observation(nx, ny):
    """기상청 격자 한 곳의 최신 초단기실황을 가져온다."""

    if not 1 <= nx <= 149 or not 1 <= ny <= 253:
        raise ValueError("NX 또는 NY가 전국 격자 범위를 벗어났습니다.")

    env = load_env()
    key = env.get("KMA_SERVICE_KEY")

    if not key:
        raise RuntimeError("KMA_SERVICE_KEY가 설정되지 않았습니다.")

    now = datetime.now(KST)

    # 초단기실황은 정시 관측 후 일정 시간이 지나 발표됨
    initial_back = 0 if now.minute >= 45 else 1

    for hours_back in range(initial_back, initial_back + 4):
        base = (now - timedelta(hours=hours_back)).replace(
            minute=0, second=0, microsecond=0
        )

        params = {
            "serviceKey": unquote(key),
            "pageNo": 1,
            "numOfRows": 100,
            "dataType": "JSON",
            "base_date": base.strftime("%Y%m%d"),
            "base_time": base.strftime("%H00"),
            "nx": nx,
            "ny": ny,
        }

        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=20,
            )
            data = response.json()
        except (requests.RequestException, ValueError):
            raise RuntimeError(
                "기상청 초단기실황 API 연결에 실패했습니다."
            ) from None

        result = data.get("response", {})
        header = result.get("header", {})
        code = str(header.get("resultCode", ""))

        if code == "03":
            continue

        if response.status_code != 200 or code != "00":
            raise RuntimeError(
                "기상청 초단기실황 API가 정상 응답하지 않았습니다."
            )

        items = (
            result.get("body", {})
            .get("items", {})
            .get("item", [])
        )

        if not items:
            continue

        first = items[0]
        observed_at = datetime.strptime(
            first["baseDate"] + first["baseTime"],
            "%Y%m%d%H%M",
        )

        values = {
            item["category"]: raw_value(item.get("obsrValue"))
            for item in items
            if (
                item.get("baseDate") == first["baseDate"]
                and item.get("baseTime") == first["baseTime"]
            )
        }

        required = {"T1H", "WSD", "VEC", "PTY", "RN1"}

        if not required.issubset(values):
            continue

        wind = numeric(values["WSD"])
        if wind is not None and wind < 0:
            wind = None

        direction = numeric(values["VEC"])
        if direction is not None and not 0 <= direction <= 360:
            direction = None

        rain = numeric(values["RN1"])
        if rain is not None and rain < 0:
            rain = None

        return {
            "source_api": "getUltraSrtNcst",
            "nx": nx,
            "ny": ny,
            "observed_at": observed_at,
            "temperature_c": numeric(values["T1H"]),
            "wind_speed_ms": wind,
            "wind_direction_deg": direction,
            "pty_raw": values["PTY"],
            "rn1_raw": values["RN1"],
            "rn1_amount_mm": rain,
            "pty_status": "RAW_UNVERIFIED",
            "rn1_status": (
                "NUMERIC_MM" if rain is not None
                else "RAW_UNVERIFIED"
            ),
            "data_quality_flags": (
                "MISSING_SOURCE_VALUE"
                if any(v is None for v in (
                    numeric(values["T1H"]),
                    wind, direction,
                    values["PTY"],
                    values["RN1"],
                ))
                else None
            ),
        }

    raise RuntimeError(
        "최근 초단기실황 관측자료를 찾지 못했습니다."
    )


def save_observation(record):
    """관측시각과 격자를 기준으로 중복 없이 저장."""

    engine = engine_for(load_env())

    try:
        with engine.begin() as conn:
            conn.execute(SAVE_SQL, record)
    finally:
        engine.dispose()


def get_current_weather(nx, ny):
    """백엔드에서 재사용할 현재 날씨 수집·저장 함수."""

    record = fetch_latest_observation(nx, ny)
    save_observation(record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nx", type=int, required=True)
    parser.add_argument("--ny", type=int, required=True)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    try:
        if args.save:
            record = get_current_weather(args.nx, args.ny)
        else:
            record = fetch_latest_observation(args.nx, args.ny)

    except Exception as exc:
        print("실행 실패:", type(exc).__name__)
        raise SystemExit(1) from None

    print("관측 시각:", record["observed_at"])
    print("격자:", record["nx"], record["ny"])
    print("기온:", record["temperature_c"])
    print("풍속:", record["wind_speed_ms"])
    print("풍향:", record["wind_direction_deg"])
    print("강수형태 원본:", record["pty_raw"])
    print("1시간 강수량:", record["rn1_amount_mm"])
    print("Oracle 저장:", "완료" if args.save else "미실행")


if __name__ == "__main__":
    main()

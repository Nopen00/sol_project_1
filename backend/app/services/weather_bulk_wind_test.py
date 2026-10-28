
import re
from datetime import datetime, timedelta
from urllib.parse import unquote

import requests

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


def main():
    env = load_env()
    key = env.get("KMA_HUB_KEY", "")

    if not key:
        print("API허브 인증키가 없습니다.")
        return

    base = get_base_datetime(
        datetime.now(KST) - timedelta(hours=3)
    )
    forecast_time = (
    base + timedelta(days=3)
).replace(hour=0, minute=0, second=0, microsecond=0)

    print("발표 시각:", base.strftime("%Y-%m-%d %H:%M"))
    print("예보 시각:", forecast_time.strftime("%Y-%m-%d %H:%M"))
    
    grids = {}


    for category, unit in [
    ("TMP", "°C"),
    ("WSD", "m/s"),
    ("VEC", "°"),
]:
        print(f"\n===== {category} 전국 자료 테스트 =====")

        params = {
            "tmfc": base.strftime("%Y%m%d%H"),
            "tmef": forecast_time.strftime("%Y%m%d%H"),
            "vars": category,
            "authKey": unquote(key),
        }

        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=60,
            )
        except requests.RequestException:
            print("API 연결 실패")
            continue

        print("HTTP 상태:", response.status_code)

        if response.status_code != 200:
            print("자료 수신 실패")
            continue

        numbers = [
            float(value)
            for value in re.findall(
                r"-?\d+(?:\.\d+)?",
                response.text,
            )
        ]

        if len(numbers) != 149 * 253:
            print("격자 구조 확인 실패:", len(numbers))
            continue
        
        grids[category] = numbers


        valid = [
            value for value in numbers
            if value != -99.0
        ]

        print("전체 격자:", len(numbers))
        print("유효한 데이터:", len(valid))

        for name, (nx, ny) in LOCATIONS.items():
            index = (ny - 1) * 149 + (nx - 1)
            value = numbers[index]

            if value == -99.0:
                print(f"{name}: 자료 없음")
            else:
                print(f"{name}: {value} {unit}")
                
    print("\n===== 기온·풍속·풍향 결합 검사 =====")

    if all(name in grids for name in ("TMP", "WSD", "VEC")):
        valid_count = 0

        for i in range(149 * 253):
            tmp = grids["TMP"][i]
            wsd = grids["WSD"][i]
            vec = grids["VEC"][i]

            if -99.0 in (tmp, wsd, vec):
                continue

            valid_count += 1

        print("세 항목 모두 존재하는 격자:", valid_count)

        for name, (nx, ny) in LOCATIONS.items():
            index = (ny - 1) * 149 + (nx - 1)

            print(
                f"{name}:",
                f"기온={grids['TMP'][index]}°C,",
                f"풍속={grids['WSD'][index]}m/s,",
                f"풍향={grids['VEC'][index]}°"
            )
    else:
        print("일부 API 조회 실패: 결합을 중단합니다.")


    print("\n테스트 종료: Oracle DB 변경 없음")


if __name__ == "__main__":
    main()

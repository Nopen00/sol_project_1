
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


def main():
    # 1. 기존 API허브 인증키 불러오기
    env = load_env()
    key = env.get("KMA_HUB_KEY", "")

    if not key:
        print("실패: 기상청 API허브 인증키가 없습니다.")
        return

    # 2. 발표 시각과 예보 시각 설정
    now = datetime.now(KST)
    base = get_base_datetime(now - timedelta(hours=3))
    forecast_time = base + timedelta(hours=6)

    params = {
        "tmfc": base.strftime("%Y%m%d%H"),
        "tmef": forecast_time.strftime("%Y%m%d%H"),
        "vars": "TMP",
        "authKey": unquote(key),
    }

    print("전국 격자자료 API 연결 테스트")
    print("발표 시각:", base.strftime("%Y-%m-%d %H:%M"))
    print("예보 시각:", forecast_time.strftime("%Y-%m-%d %H:%M"))

    # 3. 기상청 API 호출
    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=60,
        )
    except requests.RequestException:
        print("실패: API 서버 연결 오류")
        return

    print("HTTP 상태:", response.status_code)
    print("응답 크기:", len(response.content), "bytes")
    print(
        "응답 형식:",
        response.headers.get("Content-Type", ""),
    )

    if response.status_code != 200:
        print("실패: API 응답 상태를 확인해 주세요.")
        return

    # 4. 데이터 구조 확인
    lines = response.text.splitlines()

    print("전체 줄 수:", len(lines))
    print("데이터 앞부분:")

    for i, line in enumerate(lines[:3], start=1):
        safe_line = line.replace(key, "[인증키 숨김]")
        print(f"{i}: {safe_line[:120]}")

    # 5. 숫자 데이터 분석
    numbers = [
        float(value)
        for value in re.findall(
            r"-?\d+(?:\.\d+)?",
            response.text,
        )
    ]

    missing = [
        value for value in numbers
        if value == -99.0
    ]

    valid = [
        value for value in numbers
        if value != -99.0
    ]

    print()
    print("===== 전국 격자자료 분석 =====")
    print("추출된 숫자 개수:", len(numbers))
    print("결측값(-99) 개수:", len(missing))
    print("결측값 제외 숫자 개수:", len(valid))
    print("결측값 제외 숫자 예시:", valid[:10])

    expected = 149 * 253

    if len(numbers) == expected:
        print("격자 개수 37,697개와 일치합니다!")
    else:
        print("격자 개수 확인이 더 필요합니다.")
        print("예상 격자 개수:", expected)
        
        
    # 전국 격자에서 특정 지역의 기온 추출
    if len(numbers) == 149 * 253:
        locations = {
            "서울": (60, 127),
            "부산": (98, 76),
            "제주": (53, 38),
        }

        print("\n===== 지역별 기온 확인 =====")

        for name, (nx, ny) in locations.items():
            index = (ny - 1) * 149 + (nx - 1)
            temperature = numbers[index]

            if temperature == -99.0:
                print(f"{name}: 자료 없음")
            else:
                print(f"{name}: {temperature}°C")


    print("테스트 완료! Oracle DB는 수정하지 않았습니다.")

    # 전국 격자값과 기존 기상청 지역별 API 값 비교
    from backend.app.services.weather_forecast import fetch_forecast

    print("\n===== 서울 기온 교차 검증 =====")

    try:
        detail = fetch_forecast(
            env["KMA_SERVICE_KEY"],
            base,
            base,
        )

        target = (
            forecast_time.strftime("%Y%m%d"),
            forecast_time.strftime("%H%M"),
        )

        regional_temp = detail.get(target, {}).get("TMP")
        grid_index = (127 - 1) * 149 + (60 - 1)
        nationwide_temp = numbers[grid_index]

        print("전국 격자 API:", nationwide_temp, "°C")
        print("기존 지역별 API:", regional_temp, "°C")

        if regional_temp is None:
            print("비교할 지역별 예보가 없습니다.")
        elif nationwide_temp == float(regional_temp):
            print("서울 기온 일치!")
        else:
            print("값이 다릅니다. 격자 순서 등을 확인해야 합니다.")

    except RuntimeError:
        print("지역별 API 자료를 받지 못했습니다. 비교는 보류합니다.")


if __name__ == "__main__":
    main()

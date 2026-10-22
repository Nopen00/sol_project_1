def evaluate_wind(wind_speed, max_wind):
    # 날씨 정보가 없으면 판단 불가
    if wind_speed is None or max_wind is None or max_wind <= 0:
        return "UNKNOWN"

    # 드론 최대 내풍속 대비 현재 풍속 비율
    ratio = wind_speed / max_wind

    if ratio >= 0.7:
        return "NOT_RECOMMENDED"

    elif ratio >= 0.5:
        return "CAUTION"

    else:
        return "GOOD"

def evaluate_temperature(temperature, min_temp, max_temp):
    # 필수 데이터가 없으면 판단 불가
    if temperature is None or min_temp is None or max_temp is None:
        return "UNKNOWN"

    # 드론의 작동 온도 범위가 잘못된 경우
    if min_temp > max_temp:
        return "UNKNOWN"

    # 작동 가능한 온도 범위를 벗어난 경우
    if temperature < min_temp or temperature > max_temp:
        return "NOT_RECOMMENDED"

    # 0도 이하 또는 작동 한계에서 5도 이내
    if (
        temperature <= 0
        or temperature <= min_temp + 5
        or temperature >= max_temp - 5
    ):
        return "CAUTION"

    return "GOOD"

def evaluate_precipitation(pty_raw, pcp_raw):
    # 강수형태가 없으면 판단 불가
    if pty_raw is None:
        return "UNKNOWN"

    pty = str(pty_raw).strip()

    # 비, 비/눈, 눈, 소나기
    if pty in ("1", "2", "3", "4"):
        return "NOT_RECOMMENDED"

    # 알 수 없는 강수형태 코드
    if pty != "0":
        return "UNKNOWN"

    # 강수량이 없으면 판단 불가
    if pcp_raw is None:
        return "UNKNOWN"

    pcp = str(pcp_raw).strip()

    # 강수량 0
    if pcp in ("0", "0.0", "강수없음"):
        return "GOOD"

    # 1mm 미만처럼 강수가 있다는 표현
    if "미만" in pcp:
        return "NOT_RECOMMENDED"

    try:
        amount = float(pcp)

        if amount > 0:
            return "NOT_RECOMMENDED"

        if amount == 0:
            return "GOOD"

        return "UNKNOWN"

    except ValueError:
        return "UNKNOWN"

def evaluate_flight(
    wind_speed,
    max_wind,
    temperature,
    min_temp,
    max_temp,
    pty_raw,
    pcp_raw
):
    # 각각의 기상 조건 평가
    wind_result = evaluate_wind(wind_speed, max_wind)

    temp_result = evaluate_temperature(
        temperature, min_temp, max_temp
    )

    rain_result = evaluate_precipitation(pty_raw, pcp_raw)

    # 모든 평가 결과를 리스트로 저장
    results = [wind_result, temp_result, rain_result]

    # 위험도가 높은 조건부터 확인
    if "NOT_RECOMMENDED" in results:
        return "NOT_RECOMMENDED"

    if "UNKNOWN" in results:
        return "UNKNOWN"

    if "CAUTION" in results:
        return "CAUTION"

    return "GOOD"

if __name__ == "__main__":
    print(evaluate_wind(1.8, 8.0))
    print(evaluate_wind(4.0, 8.0))
    print(evaluate_wind(6.0, 8.0))
    print(evaluate_wind(None, 8.0))

    print("=== 기온 테스트 ===")
    print(evaluate_temperature(20, -10, 40))
    print(evaluate_temperature(-2, -10, 40))
    print(evaluate_temperature(37, -10, 40))
    print(evaluate_temperature(45, -10, 40))
    print(evaluate_temperature(None, -10, 40))

    print("=== 강수 테스트 ===")
    print(evaluate_precipitation("0", "0"))
    print(evaluate_precipitation("1", "0"))
    print(evaluate_precipitation("0", "2"))
    print(evaluate_precipitation("3", "1"))
    print(evaluate_precipitation("0", None))

    print("=== 최종 비행 적합도 테스트 ===")

    # 모든 조건 양호
    print(evaluate_flight(1.8, 8.0, 22.3, -10, 40, "0", "0"))

    # 풍속 주의
    print(evaluate_flight(4.0, 8.0, 22.3, -10, 40, "0", "0"))

    # 비가 오는 경우
    print(evaluate_flight(1.8, 8.0, 22.3, -10, 40, "1", "0"))

    # 강수 정보가 없는 경우
    print(evaluate_flight(1.8, 8.0, 22.3, -10, 40, None, None))

    # 강수 정보가 없어도 풍속이 위험한 경우
    print(evaluate_flight(6.0, 8.0, 22.3, -10, 40, None, None))

def evaluate_precipitation_verified(pty_raw, pty_status):
    if pty_raw is None:
        return "UNKNOWN"

    pty = str(pty_raw).strip()

    # 두 기상청 API에서 비교 확인한 코드
    if pty in ("0", "0.0"):
        return "GOOD"

    if pty in ("1", "1.0"):
        return "NOT_RECOMMENDED"

    # 아직 검증하지 않은 강수 코드는 판단 보류
    return "UNKNOWN"
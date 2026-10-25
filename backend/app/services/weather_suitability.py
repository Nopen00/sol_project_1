def evaluate_wind(wind_speed, max_wind):
    wind_speed = float(wind_speed)
    max_wind = float(max_wind)

    if wind_speed is None or max_wind is None or max_wind <= 0:
        return "UNKNOWN"
    

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
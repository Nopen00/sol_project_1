
def numeric_value(value):
    """숫자 데이터만 위험도 계산에 사용."""

    if isinstance(value, (int, float)):
        return float(value)

    return None


def calculate_risk(weather):
    level = 0
    reasons = []

    wind = numeric_value(weather.get("wind_speed"))
    rain = numeric_value(weather.get("precipitation"))
    pop = numeric_value(
        weather.get("precipitation_probability")
    )
    temp = numeric_value(weather.get("temperature"))
    snow = numeric_value(weather.get("snowfall"))

    # 기상청 자료가 부족하면 정상으로 판정하지 않음
    required = [wind, rain, pop, temp]

    if any(value is None for value in required):
        return {
            "level": None,
            "label": "확인 불가",
            "reasons": ["필수 기상 데이터 누락"],
        }

    if wind >= 12:
        level = max(level, 3)
        reasons.append("강풍 위험")
    elif wind >= 8:
        level = max(level, 2)
        reasons.append("강풍 경고")
    elif wind >= 5:
        level = max(level, 1)
        reasons.append("풍속 주의")

    if rain >= 5:
        level = max(level, 3)
        reasons.append("강수량 위험")
    elif rain >= 1:
        level = max(level, 2)
        reasons.append("강수량 경고")
    elif rain > 0:
        level = max(level, 1)
        reasons.append("강수 주의")

    if pop >= 80:
        level = max(level, 3)
        reasons.append("강수확률 위험")
    elif pop >= 60:
        level = max(level, 2)
        reasons.append("강수확률 경고")
    elif pop >= 40:
        level = max(level, 1)
        reasons.append("강수확률 주의")

    if temp <= -10 or temp >= 40:
        level = max(level, 3)
        reasons.append("극한 기온 위험")
    elif temp <= -5 or temp >= 38:
        level = max(level, 2)
        reasons.append("기온 경고")
    elif temp <= 0 or temp >= 35:
        level = max(level, 1)
        reasons.append("기온 주의")

    # 적설 자료가 있는 경우에만 판정
    if snow is not None:
        if snow >= 3:
            level = max(level, 3)
            reasons.append("적설 위험")
        elif snow >= 1:
            level = max(level, 2)
            reasons.append("적설 경고")
        elif snow > 0:
            level = max(level, 1)
            reasons.append("적설 주의")

    labels = ["정상", "주의", "경고", "위험"]

    return {
        "level": level,
        "label": labels[level],
        "reasons": reasons,
    }

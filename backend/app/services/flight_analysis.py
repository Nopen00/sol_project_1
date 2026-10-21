from app.services.drone_repository import get_drone
from app.services.weather_repository import get_weather
from app.services.weather_suitability import (
    evaluate_wind,
    evaluate_temperature,
    evaluate_precipitation_verified,
)
def analyze_flight(model_id, nx, ny):
    # 1. 드론 DB 조회
    drone = get_drone(model_id)

    if drone is None:
        return {"error": "드론 정보를 찾을 수 없습니다."}

    # 2. 날씨 DB 조회
    weather = get_weather(nx, ny)

    if weather is None:
        return {"error": "날씨 예보가 없습니다."}

    # 3. 풍속 평가
    wind_result = evaluate_wind(
        weather["wind_speed"],
        drone["max_wind"]
    )

    # 4. 기온 평가
    temp_result = evaluate_temperature(
        weather["temperature"],
        drone["min_temp"],
        drone["max_temp"]
    )

    # 5. 강수 데이터는 아직 검증되지 않았으므로 UNKNOWN
    rain_result = evaluate_precipitation_verified(
    weather["pty_raw"],
    weather["pty_status"],
)

    # 6. 최종 결과 결정
    results = [wind_result, temp_result, rain_result]

    if "NOT_RECOMMENDED" in results:
        final_result = "NOT_RECOMMENDED"
    elif "UNKNOWN" in results:
        final_result = "UNKNOWN"
    elif "CAUTION" in results:
        final_result = "CAUTION"
    else:
        final_result = "GOOD"

    return {
        "drone": drone["name"],
        "forecast_at": str(weather["forecast_at"]),
        "wind_speed": weather["wind_speed"],
        "temperature": weather["temperature"],
        "wind_result": wind_result,
        "temperature_result": temp_result,
        "precipitation_result": rain_result,
        "final_result": final_result,
        "max_wind": drone["max_wind"],
        "min_temp": drone["min_temp"],
        "max_temp": drone["max_temp"],
    }


if __name__ == "__main__":
    result = analyze_flight("AUTEL_EVO_LITE", 60, 127)
    print(result)
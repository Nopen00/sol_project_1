// /flight-analysis 응답
export interface FlightAnalysisResult {
  drone: string;
  forecast_at: string;
  wind_speed: number;
  temperature: number;
  wind_result: string;
  temperature_result: string;
  precipitation_result: string;
  final_result: string;
  max_wind: number;
  min_temp: number;
  max_temp: number;
}

// 날씨 상자에 보여 줄 값만 따로 보관하는 모양
export interface WeatherSnapshot {
  forecastAt: string;
  temperature: number;
  windSpeed: number;
}

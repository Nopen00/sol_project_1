import { getJson } from "./client";

export interface Region {
  name: string;
  province: string;
  lat: number;
  lng: number;
  level: number;
}

export interface RegionData {
  regions: Region[];
}

export async function getRegions(): Promise<RegionData> {
  return getJson<RegionData>("/regions");
}

export interface AirspaceResult { status?: string; message?: string; airspace_count?: number }
export interface WeatherResult { forecast_at?: string; temperature?: number; wind_speed?: number; precipitation?: number | string; precipitation_type?: string; precipitation_status?: string; precipitation_type_status?: string; precipitation_probability?: number; snowfall?: number | string }

export async function getAirspaceAnalysis(lat: number, lng: number) {
  return getJson<AirspaceResult>("/airspace/analysis", { latitude: lat, longitude: lng });
}

// 일반 날씨 API가 백엔드에 등록되어 있어야 합니다.
// /weather/point는 신규 API 경로 예시입니다.
export async function getWeather(lat: number, lng: number) {
  return getJson<WeatherResult>("/weather/point", { latitude: lat, longitude: lng });
}
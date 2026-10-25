import type { AirspaceAnalysis, AirspaceCollection, Drone, FlightResult, MapPoint, WeatherPoint } from "../types/mapDetails";

const BASE = "http://127.0.0.1:8001";
async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`조회 실패 (HTTP ${response.status})`);
  return response.json() as Promise<T>;
}
function query(point: MapPoint): string {
  return new URLSearchParams({ latitude: String(point.latitude), longitude: String(point.longitude) }).toString();
}
export const fetchMapWeather = (point: MapPoint) => readJson<WeatherPoint>(`${BASE}/weather/point?${query(point)}`);
export const fetchMapAirspace = (point: MapPoint) => readJson<AirspaceCollection>(`${BASE}/airspace?${query(point)}`);
export const fetchMapAirspaceAnalysis = (point: MapPoint) => readJson<AirspaceAnalysis>(`${BASE}/airspace/analysis?${query(point)}`);
export const fetchMapDrones = () => readJson<Drone[]>(`${BASE}/drones`);
export const fetchMapFlight = (point: MapPoint, modelId: string) => readJson<FlightResult>(`${BASE}/flight-analysis?${query(point)}&model_id=${encodeURIComponent(modelId)}`);

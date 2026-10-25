export interface MapPoint { latitude: number; longitude: number }
export interface WeatherPoint {
  forecast_at?: string; temperature?: number; wind_speed?: number;
  precipitation?: string | number; precipitation_type?: string;
  precipitation_status?: string; precipitation_type_status?: string;
}
export interface AirspaceAnalysis { status?: string; message?: string; airspace_count?: number }
export interface AirspaceFeature {
  properties: Record<string, unknown> & { airspace_type?: string };
  geometry: { type: string; coordinates: unknown };
}
export interface AirspaceCollection { type: string; features: AirspaceFeature[] }
export interface Drone { id: string; name: string }
export interface FlightResult {
  drone?: string; forecast_at?: string; wind_speed?: number; max_wind?: number;
  temperature?: number; min_temp?: number; max_temp?: number;
  wind_result?: string; temperature_result?: string; precipitation_result?: string; final_result?: string;
}

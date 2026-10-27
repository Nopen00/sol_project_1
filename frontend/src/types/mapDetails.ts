export interface MapPoint { latitude: number; longitude: number }
export interface WeatherPoint {
  forecast_at?: string; temperature?: number; wind_speed?: number;
  precipitation?: string | number; precipitation_type?: string;
  precipitation_status?: string; precipitation_type_status?: string;
}
export type AirspaceAnalysis = Partial<import("./map").AirspaceAnalysis>
export type AirspaceFeature = import("./map").AirspaceFeature;
export type AirspaceCollection = import("./map").AirspaceGeoJSON;
export type Drone = import("./map").DroneOption
export type FlightResult = Partial<import("./map").FlightAnalysisResult>

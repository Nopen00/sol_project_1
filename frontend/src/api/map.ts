import { getJson } from "./client";
import type { AirspaceAnalysis, AirspaceGeoJSON, DroneOption, FlightAnalysisResult } from "../types/map";
export type { AirspaceAnalysis, AirspaceGeoJSON, DroneOption, FlightAnalysisResult } from "../types/map";

export function fetchAirspaceAnalysis(latitude: number, longitude: number) {
  return getJson<AirspaceAnalysis>("/airspace/analysis", { latitude, longitude });
}
export function fetchAirspace(latitude: number, longitude: number) {
  return getJson<AirspaceGeoJSON>("/airspace", { latitude, longitude });
}
export function fetchDrones() {
  return getJson<DroneOption[]>("/drones");
}
export function fetchFlightAnalysis(modelId: string, latitude: number, longitude: number) {
  return getJson<FlightAnalysisResult>("/flight-analysis", { model_id: modelId, latitude, longitude });
}

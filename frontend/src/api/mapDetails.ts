import type { AirspaceAnalysis, AirspaceCollection, Drone, FlightResult, MapPoint, WeatherPoint } from "../types/mapDetails";
import { getJson } from "./client";
import { fetchAirspace, fetchAirspaceAnalysis, fetchDrones, fetchFlightAnalysis } from "./map";

const pointParams = (point: MapPoint) => ({ latitude: point.latitude, longitude: point.longitude });

export const fetchMapWeather = (point: MapPoint) => getJson<WeatherPoint>("/weather/point", pointParams(point));
export const fetchMapAirspace = (point: MapPoint): Promise<AirspaceCollection> => fetchAirspace(point.latitude, point.longitude);
export const fetchMapAirspaceAnalysis = (point: MapPoint): Promise<AirspaceAnalysis> => fetchAirspaceAnalysis(point.latitude, point.longitude);
export const fetchMapDrones = (): Promise<Drone[]> => fetchDrones();
export const fetchMapFlight = (point: MapPoint, modelId: string): Promise<FlightResult> => fetchFlightAnalysis(modelId, point.latitude, point.longitude);

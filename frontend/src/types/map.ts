/** API response types shared by map features and API functions. */
export interface AirspaceFeature {
  type: string;
  properties: Record<string, unknown> & {
    airspace_type?: string;
    res_lbl_1?: string; res_lbl_2?: string; res_lbl_3?: string;
    prh_lbl_1?: string; prh_lbl_2?: string; prh_lbl_3?: string; prh_lbl_4?: string;
  };
  geometry: { type: string; coordinates: number[][][][] };
}
export interface AirspaceGeoJSON { type: string; features: AirspaceFeature[] }
export interface AirspaceAnalysis { status: string; message: string; airspace_count: number }
export interface FlightAnalysisResult {
  drone?: string; forecast_at?: string; wind_speed?: number; max_wind?: number;
  temperature?: number; min_temp?: number; max_temp?: number;
  wind_result: string; temperature_result: string; precipitation_result: string; final_result: string;
}
export interface DroneOption { id: string; name: string }

import { getJson } from "./client";
export interface Region {
  name: string;
  province: string;
  lat: number;
  lng: number;
  level: number;
}

export interface RegionData {
  nationalView: {
    lat: number;
    lng: number;
    level: number;
  };
  regions: Region[];
}

export async function fetchRegions(): Promise<RegionData> {
  return getJson<RegionData>("/regions");
}
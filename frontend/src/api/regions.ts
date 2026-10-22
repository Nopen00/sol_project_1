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
  const response = await fetch("http://127.0.0.1:8001/regions");

  if (!response.ok) {
    throw new Error(`지역 목록 조회 실패: ${response.status}`);
  }

  return response.json();
}
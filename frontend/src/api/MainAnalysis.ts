const API_BASE = "http://127.0.0.1:8001";

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
  const response = await fetch(`${API_BASE}/regions`);

  if (!response.ok) {
    throw new Error(`지역 조회 실패: ${response.status}`);
  }

  return response.json();
}

export async function getAirspaceAnalysis(lat: number, lng: number) {
  const params = new URLSearchParams({
    latitude: String(lat),
    longitude: String(lng),
  });

  const response = await fetch(
    `${API_BASE}/airspace/analysis?${params}`
  );

  if (!response.ok) {
    throw new Error(`공역 조회 실패: ${response.status}`);
  }

  return response.json();
}

// 일반 날씨 API가 백엔드에 등록되어 있어야 합니다.
// /weather/point는 신규 API 경로 예시입니다.
export async function getWeather(lat: number, lng: number) {
  const params = new URLSearchParams({
    latitude: String(lat),
    longitude: String(lng),
  });

  const response = await fetch(
    `${API_BASE}/weather/point?${params}`
  );

  if (!response.ok) {
    throw new Error(`날씨 조회 실패: ${response.status}`);
  }

  return response.json();
}
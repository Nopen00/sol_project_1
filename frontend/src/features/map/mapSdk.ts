/** 지도와 장소 검색에서 하나의 Kakao SDK 인스턴스를 공유한다. */
export interface LatLng { getLat(): number; getLng(): number }
export interface MapInstance { setCenter(position: LatLng): void; getLevel(): number; getBounds(): { getSouthWest(): LatLng; getNorthEast(): LatLng } }
export interface PolygonInstance { setMap(map: MapInstance | null): void }
export interface MarkerInstance { setMap(map: MapInstance | null): void; setPosition(point: LatLng): void }
export interface KakaoMapSdk {
  load(callback: () => void): void;
  LatLng: new (lat: number, lng: number) => LatLng;
  Map: new (container: HTMLElement, options: { center: LatLng; level: number }) => MapInstance;
  Marker: new (options: { map: MapInstance; position: LatLng }) => MarkerInstance;
  Polygon: new (options: { map: MapInstance; path: LatLng[][]; strokeWeight: number; strokeColor: string; strokeOpacity: number; fillColor: string; fillOpacity: number }) => PolygonInstance;
  event: { addListener(target: MapInstance, event: "click", callback: (event: { latLng: LatLng }) => void): void; addListener(target: MapInstance, event: "idle", callback: () => void): void; removeListener(target: MapInstance, event: "idle", callback: () => void): void };
}
interface KakaoGlobal { kakao?: { maps: KakaoMapSdk } }
let loading: Promise<KakaoMapSdk> | null = null;
export function loadMapSdk(): Promise<KakaoMapSdk> {
  const global = window as Window & KakaoGlobal;
  if (global.kakao?.maps) return new Promise(resolve => global.kakao!.maps.load(() => resolve(global.kakao!.maps)));
  if (loading) return loading;
  const key = import.meta.env.VITE_KAKAO_MAP_KEY;
  if (!key) return Promise.reject(new Error("VITE_KAKAO_MAP_KEY 설정이 없습니다."));
  loading = new Promise<KakaoMapSdk>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[src*="dapi.kakao.com/v2/maps/sdk.js"]');
    const script = existing ?? document.createElement("script");
    if (!existing) script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(key)}&autoload=false&libraries=services`;
    const onReady = () => {
      if (!global.kakao?.maps) { reject(new Error("카카오 지도 SDK 초기화 실패")); return; }
      global.kakao.maps.load(() => resolve(global.kakao!.maps));
    };
    script.addEventListener("load", onReady, { once: true });
    script.addEventListener("error", () => reject(new Error("카카오 SDK 로드 실패")), { once: true });
    if (!existing) document.head.appendChild(script);
    else if (global.kakao?.maps) onReady();
  }).catch((error: unknown) => { loading = null; throw error; });
  return loading;
}

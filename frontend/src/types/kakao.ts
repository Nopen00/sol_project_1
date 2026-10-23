/** Minimal local typings for the Kakao Maps JS SDK used in MapPage.
 * No external @types/kakao.maps package is required.
 */
export interface KakaoLatLng {
  getLat(): number;
  getLng(): number;
}
export interface KakaoMouseEvent { latLng: KakaoLatLng }
export interface KakaoMap { /* opaque SDK instance */ }
export interface KakaoPolygon { setMap(map: KakaoMap | null): void }
export interface KakaoInfoWindow {
  close(): void;
  setPosition(position: KakaoLatLng): void;
  open(map: KakaoMap): void;
}
export interface KakaoMaps {
  load(callback: () => void): void;
  LatLng: new (lat: number, lng: number) => KakaoLatLng;
  Map: new (element: HTMLElement, options: { center: KakaoLatLng; level: number }) => KakaoMap;
  Polygon: new (options: {
    map: KakaoMap; path: KakaoLatLng[][]; strokeWeight: number;
    strokeColor: string; strokeOpacity: number; fillColor: string;
    fillOpacity: number; clickable: boolean;
  }) => KakaoPolygon;
  InfoWindow: new (options: { content: string }) => KakaoInfoWindow;
  event: { addListener(target: KakaoMap | KakaoPolygon, event: string, callback: (event: KakaoMouseEvent) => void): void };
}
declare global {
  interface Window { kakao?: { maps: KakaoMaps } }
}

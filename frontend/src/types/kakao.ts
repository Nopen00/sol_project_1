export interface SearchLocation {
  name: string;
  lat: number;
  lng: number;
  level: number;
}

export interface KakaoSearchDocument {
  place_name?: string;
  address_name: string;
  x: string;
  y: string;
}

export interface KakaoSearchService {
  addressSearch(query: string, callback: (results: KakaoSearchDocument[], status: string) => void): void;
}

export interface KakaoPlacesService {
  keywordSearch(query: string, callback: (results: KakaoSearchDocument[], status: string) => void): void;
}

export interface KakaoMapsSearch {
  load(callback: () => void): void;
  services: {
    Status: { OK: string; ZERO_RESULT: string };
    Geocoder: new () => KakaoSearchService;
    Places: new () => KakaoPlacesService;
  };
}

export interface KakaoSearchWindow extends Window {
  kakao?: { maps: KakaoMapsSearch };
}

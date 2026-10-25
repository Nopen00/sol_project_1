import type { KakaoSearchDocument, KakaoSearchWindow, SearchLocation } from "../../types/kakao";

let sdkPromise: Promise<void> | null = null;

function loadKakaoSearch(): Promise<void> {
  const browser = window as KakaoSearchWindow;
  if (browser.kakao?.maps?.services) {
    return new Promise<void>((resolve) => browser.kakao!.maps.load(resolve));
  }
  if (sdkPromise) return sdkPromise;

  const key = import.meta.env.VITE_KAKAO_MAP_KEY;
  if (!key) return Promise.reject(new Error("카카오 JavaScript 키가 설정되지 않았습니다."));

  sdkPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[src*="dapi.kakao.com/v2/maps/sdk.js"]');
    if (existing && !existing.src.includes("libraries=services")) {
      reject(new Error("기존 카카오 SDK에 services 라이브러리가 없습니다. 페이지를 새로고침해 주세요."));
      return;
    }
    const script = existing ?? document.createElement("script");
    if (!existing) {
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(key)}&autoload=false&libraries=services`;
    }
    const ready = () => {
      const maps = (window as KakaoSearchWindow).kakao?.maps;
      if (!maps) {
        reject(new Error("카카오맵 SDK 초기화에 실패했습니다."));
        return;
      }
      maps.load(() => {
        if (maps.services) resolve();
        else reject(new Error("카카오 검색 라이브러리를 불러오지 못했습니다. SDK 설정을 확인해 주세요."));
      });
    };
    if (existing && browser.kakao?.maps) ready();
    else {
      script.addEventListener("load", ready, { once: true });
      script.addEventListener("error", () => reject(new Error("카카오맵 SDK 로딩에 실패했습니다.")), { once: true });
      if (!existing) document.head.appendChild(script);
    }
  }).catch((error: unknown) => {
    sdkPromise = null;
    throw error;
  });
  return sdkPromise;
}

function convertLocation(document: KakaoSearchDocument, fallback: string): SearchLocation {
  const lat = Number(document.y);
  const lng = Number(document.x);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) throw new Error("검색 결과의 좌표가 올바르지 않습니다.");
  return { name: document.place_name || document.address_name || fallback, lat, lng, level: 6 };
}

export async function searchKakaoLocation(keyword: string): Promise<SearchLocation> {
  await loadKakaoSearch();
  const services = (window as KakaoSearchWindow).kakao?.maps.services;
  if (!services) throw new Error("카카오 검색 서비스를 사용할 수 없습니다.");

  const address = await new Promise<KakaoSearchDocument | null>((resolve, reject) => {
    new services.Geocoder().addressSearch(keyword, (results, status) => {
      if (status === services.Status.OK && results.length) resolve(results[0]);
      else if (status === services.Status.ZERO_RESULT) resolve(null);
      else reject(new Error("주소 검색 중 오류가 발생했습니다."));
    });
  });
  if (address) return convertLocation(address, keyword);

  const place = await new Promise<KakaoSearchDocument | null>((resolve, reject) => {
    new services.Places().keywordSearch(keyword, (results, status) => {
      if (status === services.Status.OK && results.length) resolve(results[0]);
      else if (status === services.Status.ZERO_RESULT) resolve(null);
      else reject(new Error("장소 검색 중 오류가 발생했습니다."));
    });
  });
  if (!place) throw new Error("검색 결과가 없습니다. 주소나 장소명을 다시 입력해주세요.");
  return convertLocation(place, keyword);
}

/** Return live place suggestions from Kakao, rather than fixed keywords. */
export async function suggestKakaoLocations(keyword: string): Promise<SearchLocation[]> {
  const query = keyword.trim();
  if (query.length < 2) return [];

  await loadKakaoSearch();
  const services = (window as KakaoSearchWindow).kakao?.maps.services;
  if (!services) throw new Error("카카오 검색 서비스를 사용할 수 없습니다.");

  return new Promise<SearchLocation[]>((resolve, reject) => {
    new services.Places().keywordSearch(query, (results, status) => {
      if (status === services.Status.ZERO_RESULT) {
        resolve([]);
      } else if (status === services.Status.OK) {
        resolve(results.slice(0, 5).map((result) => convertLocation(result, query)));
      } else {
        reject(new Error("추천 장소 검색에 실패했습니다."));
      }
    });
  });
}


/** Resolve the road/parcel address at a clicked map coordinate. */
export async function getAddressFromCoords(latitude: number, longitude: number): Promise<string> {
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    throw new Error("좌표가 올바르지 않습니다.");
  }
  await loadKakaoSearch();
  const services = (window as KakaoSearchWindow).kakao?.maps.services;
  if (!services) throw new Error("카카오 주소 검색 서비스를 사용할 수 없습니다.");

  type AddressItem = {
    road_address?: { address_name?: string } | null;
    address?: { address_name?: string } | null;
  };
  type ReverseGeocoder = {
    coord2Address: (
      longitude: number, latitude: number,
      callback: (result: AddressItem[], status: string) => void
    ) => void;
  };
  const Geocoder = services.Geocoder as unknown as new () => ReverseGeocoder;
  return new Promise<string>((resolve, reject) => {
    new Geocoder().coord2Address(longitude, latitude, (results, status) => {
      if (status === services.Status.OK && results.length > 0) {
        resolve(results[0].road_address?.address_name || results[0].address?.address_name || "주소 정보 없음");
      } else if (status === services.Status.ZERO_RESULT) {
        resolve("주소 정보 없음");
      } else {
        reject(new Error("좌표의 주소를 조회하지 못했습니다."));
      }
    });
  });
}

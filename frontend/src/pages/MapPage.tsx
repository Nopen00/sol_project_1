import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Navigate, useParams, useSearchParams } from "react-router-dom";
import { fetchMapAirspace, fetchMapAirspaceAnalysis, fetchMapDrones, fetchMapFlight, fetchMapWeather } from "../api/mapDetails";
import { getAddressFromCoords, searchKakaoLocation, suggestKakaoLocations } from "../features/map/kakaoSearch";
import { loadMapSdk, type KakaoMapSdk, type MapInstance, type MarkerInstance, type PolygonInstance } from "../features/map/mapSdk";
import type { SearchLocation } from "../types/kakao";
import type { AirspaceAnalysis, AirspaceCollection, Drone, FlightResult, MapPoint, WeatherPoint } from "../types/mapDetails";
import "./MapPage.css";

const MODES = ["restricted", "weather", "suitability"];
const LAYERS = [
  { id: "restricted", label: "비행금지·제한구역", icon: "🚫" },
  { id: "weather", label: "날씨", icon: "☀️" },
  { id: "suitability", label: "비행 적합도", icon: "📊" },
  { id: "grid", label: "격자", icon: "🏁" },
];
function parsePoint(params: URLSearchParams): MapPoint | null {
  const lat = params.get("lat"), lng = params.get("lng");
  if (lat === null || lng === null || !lat.trim() || !lng.trim()) return null;
  const latitude = Number(lat), longitude = Number(lng);
  return Number.isFinite(latitude) && Number.isFinite(longitude) && latitude >= 33 && latitude <= 39 && longitude >= 124 && longitude <= 132
    ? { latitude, longitude } : null;
}
function polygonRings(geometry: { type: string; coordinates: unknown }): number[][][][] {
  if (geometry.type === "Polygon" && Array.isArray(geometry.coordinates)) return [geometry.coordinates as number[][][]];
  if (geometry.type === "MultiPolygon" && Array.isArray(geometry.coordinates)) return geometry.coordinates as number[][][][];
  return [];
}
function grade(status?: string): string {
  if (status === "GOOD") return "🟢 양호";
  if (status === "CAUTION") return "🟠 주의";
  if (status === "NOT_RECOMMENDED") return "🔴 비행 비권장";
  return "⚪ 판단 불가";
}
export function MapView({ mode }: { mode: string }) {
  const [params] = useSearchParams();
  const initialPoint = parsePoint(params);
  const [point, setPoint] = useState<MapPoint | null>(initialPoint);
  const [locationName, setLocationName] = useState(params.get("region") || "선택 위치");
  const addressRequestRef = useRef(0);
  const [searchText, setSearchText] = useState("");
  const [suggestions, setSuggestions] = useState<SearchLocation[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<SearchLocation | null>(null);
  const [searchError, setSearchError] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [layers, setLayers] = useState<string[]>(initialPoint ? ["restricted", "weather"] : [mode]);
  const [weather, setWeather] = useState<WeatherPoint | null>(null);
  const [airspace, setAirspace] = useState<AirspaceAnalysis | null>(null);
  const [weatherError, setWeatherError] = useState("");
  const [airspaceError, setAirspaceError] = useState("");
  const [loading, setLoading] = useState(false);
  const [drones, setDrones] = useState<Drone[]>([]);
  const [selectedDrone, setSelectedDrone] = useState("");
  const [flight, setFlight] = useState<FlightResult | null>(null);
  const [flightError, setFlightError] = useState("");
  const [flightLoading, setFlightLoading] = useState(false);
  const mapElement = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapInstance | null>(null);
  const sdkRef = useRef<KakaoMapSdk | null>(null);
  const markerRef = useRef<MarkerInstance | null>(null);
  const polygonsRef = useRef<PolygonInstance[]>([]);
  const airspaceDataRef = useRef<AirspaceCollection | null>(null);
  const requestRef = useRef(0);
  const layersRef = useRef(layers);
  layersRef.current = layers;

  useEffect(() => {
    const query = searchText.trim();
    if (!showSuggestions || query.length < 2) { setSuggestions([]); setSuggestionLoading(false); return; }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      setSuggestionLoading(true);
      void suggestKakaoLocations(query).then(results => {
        if (!cancelled) setSuggestions(results);
      }).catch(() => { if (!cancelled) setSuggestions([]); }).finally(() => {
        if (!cancelled) setSuggestionLoading(false);
      });
    }, 350);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [searchText, showSuggestions]);

  const clearPolygons = useCallback(() => {
    polygonsRef.current.forEach(polygon => polygon.setMap(null));
    polygonsRef.current = [];
  }, []);

  const drawAirspace = useCallback((data: AirspaceCollection) => {
    const sdk = sdkRef.current, map = mapRef.current;
    if (!sdk || !map) return;
    clearPolygons();
    airspaceDataRef.current = data;
    data.features.forEach(feature => {
      const color = feature.properties.airspace_type === "P" ? "#8b1e2d" : "#8050b9";
      polygonRings(feature.geometry).forEach(rings => {
        const path = rings.map(ring => ring.filter(pair => pair.length >= 2 && pair.every(Number.isFinite)).map(pair => new sdk.LatLng(pair[1], pair[0]))).filter(ring => ring.length >= 3);
        if (!path.length) return;
        polygonsRef.current.push(new sdk.Polygon({ map, path, strokeWeight: 2, strokeColor: color, strokeOpacity: 0.9, fillColor: color, fillOpacity: 0.25 }));
      });
    });
  }, [clearPolygons]);

  const selectPoint = useCallback((selected: MapPoint, updateAddress = true) => {
    if (updateAddress) {
      const requestId = ++addressRequestRef.current;
      setLocationName("주소 조회 중...");
      void getAddressFromCoords(selected.latitude, selected.longitude)
        .then(address => { if (requestId === addressRequestRef.current) setLocationName(address); })
        .catch(() => { if (requestId === addressRequestRef.current) setLocationName("주소 정보 없음"); });
    }
    setPoint(selected);
    setFlight(null);
    const sdk = sdkRef.current, map = mapRef.current;
    if (sdk && map) {
      const position = new sdk.LatLng(selected.latitude, selected.longitude);
      map.setCenter(position);
      if (markerRef.current) markerRef.current.setPosition(position);
      else markerRef.current = new sdk.Marker({ map, position });
    }
  }, []);

  async function handleLocationSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = searchText.trim();
    if (!query) { setSearchError("지역명이나 장소명을 입력하세요."); return; }
    setSearchLoading(true);
    setSearchError("");
    setShowSuggestions(false);
    try {
      const location = selectedSuggestion && selectedSuggestion.name === query
        ? selectedSuggestion : await searchKakaoLocation(query);
      // 기존 지도 클릭과 같은 경로로 좌표, 마커, 날씨, 공역 정보를 갱신합니다.
      ++addressRequestRef.current;
      setLocationName(location.name);
      selectPoint({ latitude: location.lat, longitude: location.lng }, false);
      setLayers(current => Array.from(new Set([...current, "restricted", "weather"])));
      setSuggestions([]);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "위치 검색에 실패했습니다.");
    } finally { setSearchLoading(false); }
  }

  useEffect(() => {
    let cancelled = false;
    loadMapSdk().then(sdk => {
      if (cancelled || !mapElement.current) return;
      sdkRef.current = sdk;
      const initial = parsePoint(params) ?? { latitude: 37.5665, longitude: 126.978 };
      const zoom = Number(params.get("level"));
      const level = Number.isInteger(zoom) && zoom >= 1 && zoom <= 14 ? zoom : 6;
      const map = new sdk.Map(mapElement.current, { center: new sdk.LatLng(initial.latitude, initial.longitude), level });
      mapRef.current = map;
      if (airspaceDataRef.current) drawAirspace(airspaceDataRef.current);
      if (parsePoint(params)) selectPoint(initial, false);
      sdk.event.addListener(map, "click", event => selectPoint({ latitude: event.latLng.getLat(), longitude: event.latLng.getLng() }));
    }).catch(error => { if (!cancelled) setAirspaceError(error instanceof Error ? error.message : "지도 로딩 실패"); });
    return () => { cancelled = true; addressRequestRef.current += 1; requestRef.current += 1; clearPolygons(); markerRef.current?.setMap(null); markerRef.current = null; mapRef.current = null; };
  }, [clearPolygons, drawAirspace, params, selectPoint]);

  useEffect(() => {
    const id = ++requestRef.current;
    clearPolygons();
    airspaceDataRef.current = null;
    setAirspace(null); setWeather(null); setAirspaceError(""); setWeatherError("");
    if (!point) return;
    const tasks: Promise<void>[] = [];
    if (layers.includes("restricted")) {
      tasks.push(fetchMapAirspaceAnalysis(point).then(value => { if (id === requestRef.current) setAirspace(value); }).catch(() => { if (id === requestRef.current) setAirspaceError("공역 분석 정보를 조회하지 못했습니다."); }));
      tasks.push(fetchMapAirspace(point).then(value => { if (id === requestRef.current) drawAirspace(value); }).catch(() => { if (id === requestRef.current) setAirspaceError("공역 경계 데이터를 조회하지 못했습니다."); }));
    }
    if (layers.includes("weather")) tasks.push(fetchMapWeather(point).then(value => { if (id === requestRef.current) setWeather(value); }).catch(() => { if (id === requestRef.current) setWeatherError("해당 좌표의 날씨 예보를 조회하지 못했습니다."); }));
    setLoading(tasks.length > 0);
    void Promise.allSettled(tasks).then(() => { if (id === requestRef.current) setLoading(false); });
    return () => { requestRef.current += 1; };
  }, [point?.latitude, point?.longitude, layers, clearPolygons, drawAirspace]);

  useEffect(() => { void fetchMapDrones().then(setDrones).catch(() => setDrones([])); }, []);
  async function analyzeFlight() {
    if (!point || !selectedDrone) { setFlightError("위치와 드론을 먼저 선택하세요."); return; }
    setFlightLoading(true); setFlightError(""); setFlight(null);
    try { setFlight(await fetchMapFlight(point, selectedDrone)); }
    catch { setFlightError("비행 적합도 분석에 실패했습니다."); }
    finally { setFlightLoading(false); }
  }
  return (
    <section>
      <h1>{mode} 지도</h1>
      <div className="map-location-search">
        <form className="map-location-search-form" onSubmit={event => void handleLocationSearch(event)}>
          <input
            type="search"
            aria-label="지역명 또는 주소 검색"
            aria-autocomplete="list"
            aria-expanded={showSuggestions && searchText.trim().length >= 2}
            aria-controls="map-location-suggestion-list"
            placeholder="지역명, 주소 또는 장소 입력 (예: 서울 강남구)"
            autoComplete="off"
            value={searchText}
            onFocus={() => setShowSuggestions(true)}
            onChange={event => {
              setSearchText(event.target.value);
              setSelectedSuggestion(null);
              setSuggestions([]);
              setShowSuggestions(true);
              setSuggestionLoading(false);
              setSearchError("");
            }}
            onKeyDown={event => {
              if (event.key === "Escape") setShowSuggestions(false);
            }}
          />
          <button type="submit" disabled={searchLoading}>{searchLoading ? "검색 중..." : "검색"}</button>
        </form>
        {showSuggestions && searchText.trim().length >= 2 && (
          <div id="map-location-suggestion-list" className="map-location-suggestions" role="listbox" aria-label="추천 장소">
            {suggestionLoading ? <div className="map-location-suggestion-message">검색 중...</div> :
              suggestions.length ? suggestions.map((place, index) => (
                <button key={`${place.lat}-${place.lng}-${index}`} type="button" role="option" aria-selected={false}
                  onClick={() => { setSearchText(place.name); setSelectedSuggestion(place); setShowSuggestions(false); }}>
                  📍 {place.name}
                </button>
              )) : <div className="map-location-suggestion-message">추천 장소가 없습니다.</div>}
          </div>
        )}
        {searchError && <p className="map-location-search-error" role="alert">{searchError}</p>}
      </div>
      <div className="map-box">
        <div ref={mapElement} className="kakao-map-canvas" aria-label="드론 비행 지도" />
        <div className="layer-toggle">
          {LAYERS.map(layer => <button key={layer.id} type="button" title={layer.label} aria-label={layer.label} aria-pressed={layers.includes(layer.id)} className={`layer-btn ${layers.includes(layer.id) ? "layer-btn--on" : ""}`} onClick={() => setLayers(current => current.includes(layer.id) ? current.filter(id => id !== layer.id) : [...current, layer.id])}>{layer.icon}</button>)}
        </div>
      </div>
      <div className="map-details">
        <h2>선택한 위치 정보</h2>
        <p>{locationName} {point ? `· 위도 ${point.latitude.toFixed(5)}, 경도 ${point.longitude.toFixed(5)}` : "· 지도에서 위치를 클릭하세요."}</p>
        {loading && <p>정보 조회 중...</p>}
        <div className="map-details-grid">
          {layers.includes("restricted") && <article className="map-details-card"><h3>비행 공역</h3>{airspaceError && <p role="alert">{airspaceError}</p>}{airspace && <><p>{airspace.status === "PROHIBITED_AIRSPACE" ? "🚫 비행금지구역" : airspace.status === "RESTRICTED_AIRSPACE" ? "⚠️ 비행제한구역" : "🔎 추가 확인 필요"}</p><p>{airspace.message}</p><p>조회 공역: {airspace.airspace_count ?? 0}개</p></>}</article>}
          {layers.includes("weather") && <article className="map-details-card"><h3>날씨 및 예보 날짜</h3>{weatherError && <p role="alert">{weatherError}</p>}{weather && <><p><strong>예보 시각:</strong> {weather.forecast_at ?? "정보 없음"}</p><p>기온: {weather.temperature ?? "-"}°C</p><p>풍속: {weather.wind_speed ?? "-"} m/s</p><p>강수량: {weather.precipitation ?? "-"}</p><p>강수 형태: {weather.precipitation_type ?? "-"}</p></>}</article>}
        </div>
        {layers.includes("suitability") && <article className="map-details-card"><h3>드론 비행 적합도</h3><select aria-label="드론 선택" value={selectedDrone} onChange={event => setSelectedDrone(event.target.value)}><option value="">드론 선택</option>{drones.map(drone => <option key={drone.id} value={drone.id}>{drone.name}</option>)}</select><button type="button" disabled={!point || !selectedDrone || flightLoading} onClick={() => void analyzeFlight()}>{flightLoading ? "분석 중..." : "비행 적합도 분석"}</button>{flightError && <p role="alert">{flightError}</p>}{flight && <><p>드론: {flight.drone ?? "-"}</p><p>예보 시각: {flight.forecast_at ?? "-"}</p><p>풍속: {flight.wind_speed ?? "-"} m/s / 최대 {flight.max_wind ?? "-"} m/s · {grade(flight.wind_result)}</p><p>기온: {flight.temperature ?? "-"}°C · {grade(flight.temperature_result)}</p><p>강수 평가: {grade(flight.precipitation_result)}</p><strong>최종 결과: {grade(flight.final_result)}</strong></>}</article>}
        <p className="map-details-notice">이 정보는 참고용입니다. 실제 비행 승인은 최신 공식 정보로 확인하세요.</p>
      </div>
    </section>
  );
}
export default function MapPage() {
  const { mode } = useParams();
  if (!mode || !MODES.includes(mode)) return <Navigate to="/" replace />;
  return <MapView mode={mode} />;
}

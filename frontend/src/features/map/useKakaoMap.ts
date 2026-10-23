import { useEffect, useRef, useState } from "react";
import { fetchAirspace, fetchAirspaceAnalysis } from "../../api/map";
import { getWeather } from "../../api/MainAnalysis";
import type { WeatherResult } from "../../api/MainAnalysis";
import type { AirspaceAnalysis, AirspaceFeature } from "../../types/map";
import type { KakaoInfoWindow, KakaoMouseEvent, KakaoPolygon } from "../../types/kakao";

/** Kakao SDK lifecycle, map clicks and airspace overlays. UI stays in MapPage. */
function escapeHtml(value: unknown): string {
  return String(value ?? "정보 없음").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char] ?? char);
}

export function useKakaoMap(activeLayers: string[]) {
  const [selectedLocation, setSelectedLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);

  const [weatherResult, setWeatherResult] = useState<WeatherResult | null>(null);
  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const weatherRequestId = useRef(0);
  const mapReadyRef = useRef(false);
  const queryLocationRef = useRef<{latitude: number; longitude: number} | null>(null);
  const requestAtRef = useRef<(latitude: number, longitude: number) => void>(() => {});

  const [airspaceResult, setAirspaceResult] = useState<AirspaceAnalysis | null>(null);

  // 가장 최근에 클릭한 요청 번호를 저장
  const [airspaceError, setAirspaceError] = useState<string | null>(null);
  const analysisRequestId = useRef(0);
  const polygonsRef = useRef<KakaoPolygon[]>([]);
  const infoWindowRef = useRef<KakaoInfoWindow | null>(null);
  const activeLayersRef = useRef(activeLayers);

  useEffect(() => {
    activeLayersRef.current = activeLayers;
  }, [activeLayers]);

  useEffect(() => {
    const kakaoKey = import.meta.env.VITE_KAKAO_MAP_KEY;

    if (!kakaoKey) {
      console.error("카카오맵 API 키가 없습니다.");
      return;
    }

    let disposed = false;
    const script = document.createElement("script");

    script.src =
      `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(kakaoKey)}&autoload=false`;

    script.onload = () => {
      if (disposed) return;
      const kakao = window.kakao;

      if (!kakao) {
        console.error("카카오맵 SDK 객체가 없습니다.");
        return;
      }

      kakao.maps.load(() => {
        if (disposed) return;
        const container = document.getElementById("kakao-map");

        if (!container) return;

       
        // 메인 페이지에서 전달한 지역 좌표 읽기
          const params = new URLSearchParams(window.location.search);

          const latParam = params.get("lat");
          const lngParam = params.get("lng");
          const levelParam = params.get("level");

          // 기본 지도 위치: 서울
          let latitude = 37.5665;
          let longitude = 126.9780;
          let level = 7;

          // URL에 유효한 좌표가 있을 때만 초기 위치로 사용합니다.
          let hasInitialLocation = false;
          if (latParam !== null && lngParam !== null) {
            const lat = Number(latParam);
            const lng = Number(lngParam);
            const zoom = levelParam === null ? 6 : Number(levelParam);

            if (
              Number.isFinite(lat) &&
              Number.isFinite(lng) &&
              lat >= 33 &&
              lat <= 39 &&
              lng >= 124 &&
              lng <= 132
            ) {
              latitude = lat;
              longitude = lng;
              hasInitialLocation = true;

              if (
                Number.isFinite(zoom) &&
                zoom >= 1 &&
                zoom <= 14
              ) {
                level = zoom;
              }
            }
          }

          // 전달받은 좌표로 카카오맵 생성
          const options = {
            center: new kakao.maps.LatLng(latitude, longitude),
            level,
          };

          const map = new kakao.maps.Map(container, options);

          console.log("지도 초기 위치:", {
            latitude,
            longitude,
            level,
          });


        mapReadyRef.current = true;
        const requestAt = (latitude: number, longitude: number) => {
          queryLocationRef.current = { latitude, longitude };
          setSelectedLocation({ latitude, longitude });
          const requestId = ++analysisRequestId.current;
          const weatherId = ++weatherRequestId.current;
          polygonsRef.current.forEach((polygon) => polygon.setMap(null));
          polygonsRef.current = [];
          infoWindowRef.current?.close();
          infoWindowRef.current = null;
          setAirspaceResult(null);
          setAirspaceError(null);
          setWeatherResult(null);
          setWeatherError(null);
          setWeatherLoading(false);

          if (activeLayersRef.current.includes("weather")) {
            setWeatherLoading(true);
            getWeather(latitude, longitude)
              .then((data) => { if (weatherId === weatherRequestId.current) setWeatherResult(data); })
              .catch((error) => {
                if (weatherId !== weatherRequestId.current) return;
                console.error("날씨 조회 실패:", error);
                setWeatherError("해당 위치의 날씨 예보를 불러오지 못했습니다.");
              })
              .finally(() => { if (weatherId === weatherRequestId.current) setWeatherLoading(false); });
          }

          if (!activeLayersRef.current.includes("restricted")) return;
          fetchAirspaceAnalysis(latitude, longitude)
            .then((data) => { if (requestId === analysisRequestId.current) setAirspaceResult(data); })
            .catch((error) => {
              if (requestId !== analysisRequestId.current) return;
              console.error("공역 분석 실패:", error);
              setAirspaceError("공역 분석에 실패했습니다. 잠시 후 다시 시도해 주세요.");
            });
          fetchAirspace(latitude, longitude)
            .then((data) => {
              if (requestId !== analysisRequestId.current) return;
              data.features.forEach((feature: AirspaceFeature) => {
                console.log("공역 종류:", feature.properties.airspace_type);
                console.log("공역 이름:", feature.properties);
                console.log("도형 종류:", feature.geometry.type);
                console.log("좌표:", feature.geometry.coordinates);

                if (feature.geometry.type === "MultiPolygon") {
                  feature.geometry.coordinates.forEach((polygon: number[][][]) => {
                    const paths = polygon.map((ring: number[][]) =>
                      ring.map(
                        (coordinate: number[]) =>
                          new kakao.maps.LatLng(coordinate[1], coordinate[0])
                      )
                    );

                    const airspaceType = feature.properties.airspace_type;

                    const color = airspaceType === "P" ? "#8B0000" : "#800080";

                    const airspacePolygon = new kakao.maps.Polygon({
                      map: map,
                      path: paths,
                      strokeWeight: 3,
                      strokeColor: color,
                      strokeOpacity: 0.9,
                      fillColor: color,
                      fillOpacity: 0.25,
                      clickable: true,
                    });

                    polygonsRef.current.push(airspacePolygon);

                    kakao.maps.event.addListener(
                      airspacePolygon,
                      "click",
                      (mouseEvent: KakaoMouseEvent) => {


                        if (infoWindowRef.current) {
                          infoWindowRef.current.close();
                          infoWindowRef.current = null;
                        }

                        const properties = feature.properties;

                        console.log("선택한 공역 정보:", properties);


                        const isRestricted = airspaceType === "R";

                        const airspaceName = isRestricted
                          ? properties.res_lbl_1
                          : properties.prh_lbl_1;

                        const upperAltitude = isRestricted
                          ? properties.res_lbl_2
                          : properties.prh_lbl_2;

                        const lowerAltitude = isRestricted
                          ? properties.res_lbl_3
                          : properties.prh_lbl_3;

                        const airspaceDescription = isRestricted
                          ? "비행제한구역"
                          : properties.prh_lbl_4 ?? "비행금지구역";

                        const infoWindow = new kakao.maps.InfoWindow({
                          content: `
    <div style="padding:12px;min-width:220px;">
      <strong>${airspaceType === "P" ? "비행금지구역" : "비행제한구역"}</strong>
      <p>구역명: ${escapeHtml(airspaceName)}</p>
      <p>상한 고도: ${escapeHtml(upperAltitude)}</p>
      <p>하한 고도: ${escapeHtml(lowerAltitude)}</p>
      <p>구역 설명: ${escapeHtml(airspaceDescription)}</p>
    </div>
  `,
                        });

                        infoWindow.setPosition(mouseEvent.latLng);
                        infoWindow.open(map);
                        infoWindowRef.current = infoWindow;
                      }
                    );
                  });
                }
              });
            })
            .catch((error) => {
              if (requestId !== analysisRequestId.current) return;
              console.error("공역 조회 실패:", error);
              setAirspaceError("공역 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
            });
        };
        requestAtRef.current = requestAt;
        kakao.maps.event.addListener(map, "click", (mouseEvent: KakaoMouseEvent) => {
          requestAt(mouseEvent.latLng.getLat(), mouseEvent.latLng.getLng());
        });
        // 메인페이지에서 받은 좌표를 지도 클릭과 동일한 조회 함수로 처리합니다.
        // SDK 로딩 후 호출하므로 지도 생성 전 요청되는 문제를 방지합니다.
        if (hasInitialLocation) {
          requestAt(latitude, longitude);
        }
      });
    };

    script.onerror = () => {
      console.error("카카오맵 SDK를 불러오지 못했습니다.");
    };

    document.head.appendChild(script);

    return () => {
      disposed = true;
      analysisRequestId.current += 1;
      weatherRequestId.current += 1;
      mapReadyRef.current = false;
      requestAtRef.current = () => {};
      polygonsRef.current.forEach((polygon) => polygon.setMap(null));
      polygonsRef.current = [];
      infoWindowRef.current?.close();
      script.remove();
    };
  }, []);
  // 레이어 토글 시 선택한 위치의 데이터를 다시 조회하고 비활성 레이어는 즉시 제거.
  useEffect(() => {
    activeLayersRef.current = activeLayers;
    if (mapReadyRef.current && queryLocationRef.current) {
      const { latitude, longitude } = queryLocationRef.current;
      requestAtRef.current(latitude, longitude);
    }
  }, [activeLayers]);

  return { selectedLocation, airspaceResult, airspaceError, weatherResult, weatherError, weatherLoading };
}

import { Navigate, useParams } from "react-router-dom";
import "./MapPage.css";
import { useEffect, useRef, useState } from "react";
import InfoBox from "../components/InfoBox";
import DroneSelect from "../features/weather/DroneSelect";
import { getDroneModels } from "../api/droneApi";
import type { DroneModel } from "../types/drone";

const MODES = ["restricted", "weather", "suitability"];
const LAYERS = [
  { id: "restricted", label: "비행제한구역", icon: "🚫" },
  { id: "weather", label: "날씨", icon: "☀️" },
  { id: "suitability", label: "비행 적합도", icon: "📊" },
  { id: "grid", label: "격자 on/off", icon: "🏁" },
];

export function MapView({ mode }: { mode: string }) {
  const [activeLayers, setActiveLayers] = useState<string[]>(
    mode ? [mode] : [],
  );
  const [drones, setDrones] = useState<DroneModel[]>([]);
  const [selectedDroneId, setSelectedDroneId] = useState("");

  const [airspaceResult, setAirspaceResult] = useState<{
    status: string;
    message: string;
    airspace_count: number;
  } | null>(null);
  useEffect(() => {
    let cancelled = false;

    getDroneModels().then((models) => {
      if (!cancelled) setDrones(models);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // 가장 최근에 클릭한 요청 번호를 저장
  const [airspaceError, setAirspaceError] = useState<string | null>(null);
  const analysisRequestId = useRef(0);
  const polygonsRef = useRef<any[]>([]);
  const infoWindowRef = useRef<any>(null);
  const activeLayersRef = useRef(activeLayers);

  useEffect(() => {
    activeLayersRef.current = activeLayers;
  }, [activeLayers]);

  const toggleLayer = (id: string) => {
    if (activeLayers.includes(id)) {
      setActiveLayers(activeLayers.filter((layerId) => layerId !== id)); // 빼기: 그 id만 빠진 새 배열
    } else {
      setActiveLayers([...activeLayers, id]); // 넣기: 기존 + 그 id 가 있는 새 배열
    }
  };

  useEffect(() => {
    const kakaoKey = import.meta.env.VITE_KAKAO_MAP_KEY;

    if (!kakaoKey) {
      console.error("카카오맵 API 키가 없습니다.");
      return;
    }

    const script = document.createElement("script");

    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(kakaoKey)}&autoload=false`;

    script.onload = () => {
      const kakao = (window as any).kakao;

      kakao.maps.load(() => {
        const container = document.getElementById("kakao-map");

        if (!container) return;

        const options = {
          center: new kakao.maps.LatLng(37.5665, 126.978),
          level: 7,
        };

        const map = new kakao.maps.Map(container, options);

        kakao.maps.event.addListener(map, "click", (mouseEvent: any) => {
          const requestId = ++analysisRequestId.current;
          setAirspaceResult(null);
          setAirspaceError(null);
          polygonsRef.current.forEach((polygon) => {
            polygon.setMap(null);
          });

          polygonsRef.current = [];

          if (!activeLayersRef.current.includes("restricted")) {
            return;
          }
          const latlng = mouseEvent.latLng;

          const latitude = latlng.getLat();
          const longitude = latlng.getLng();

          console.log("클릭한 위치");
          console.log("위도:", latitude);
          console.log("경도:", longitude);

          fetch(
            `http://127.0.0.1:8000/airspace/analysis?longitude=${longitude}&latitude=${latitude}`,
          )
            .then((response) => {
              if (!response.ok) {
                throw new Error(`HTTP 오류: ${response.status}`);
              }

              return response.json();
            })
            .then((data) => {
              if (requestId !== analysisRequestId.current) return;

              console.log("공역 분석 결과:", data);
              setAirspaceResult(data);
            })
            .catch((error) => {
              if (requestId !== analysisRequestId.current) return;

              console.error("공역 분석 실패:", error);
              setAirspaceError(
                "공역 분석에 실패했습니다. 잠시 후 다시 시도해 주세요.",
              );
            });

          fetch(
            `http://127.0.0.1:8000/airspace?longitude=${longitude}&latitude=${latitude}`,
          )
            .then((response) => {
              if (!response.ok) {
                throw new Error(`HTTP 오류: ${response.status}`);
              }
              return response.json();
            })
            .then((data) => {
              if (requestId !== analysisRequestId.current) return;

              console.log("공역 조회 결과:", data);
              console.log("공역 개수:", data.features.length);

              data.features.forEach((feature: any) => {
                console.log("공역 종류:", feature.properties.airspace_type);
                console.log("공역 이름:", feature.properties);
                console.log("도형 종류:", feature.geometry.type);
                console.log("좌표:", feature.geometry.coordinates);

                if (feature.geometry.type === "MultiPolygon") {
                  feature.geometry.coordinates.forEach(
                    (polygon: number[][][]) => {
                      const paths = polygon.map((ring: number[][]) =>
                        ring.map(
                          (coordinate: number[]) =>
                            new kakao.maps.LatLng(coordinate[1], coordinate[0]),
                        ),
                      );

                      const airspaceType = feature.properties.airspace_type;

                      const color =
                        airspaceType === "P" ? "#FF0000" : "#FFA500";

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
                        (mouseEvent: any) => {
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
                            : (properties.prh_lbl_4 ?? "비행금지구역");

                          const infoWindow = new kakao.maps.InfoWindow({
                            content: `
    <div style="padding:12px;min-width:220px;">
      <strong>${airspaceType === "P" ? "비행금지구역" : "비행제한구역"}</strong>
      <p>구역명: ${airspaceName ?? "정보 없음"}</p>
      <p>상한 고도: ${upperAltitude ?? "정보 없음"}</p>
      <p>하한 고도: ${lowerAltitude ?? "정보 없음"}</p>
      <p>구역 설명: ${airspaceDescription}</p>
    </div>
  `,
                          });

                          infoWindow.setPosition(mouseEvent.latLng);
                          infoWindow.open(map);
                          infoWindowRef.current = infoWindow;
                        },
                      );
                    },
                  );
                }
              });
            })
            .catch((error) => {
              if (requestId !== analysisRequestId.current) return;

              console.error("공역 조회 실패:", error);
              setAirspaceError(
                "공역 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",
              );
            });
        });
      });
    };

    script.onerror = () => {
      console.error("카카오맵 SDK를 불러오지 못했습니다.");
    };

    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, []);
  useEffect(() => {
    if (!activeLayers.includes("restricted")) {
      // 이전 API 요청의 응답 무시
      analysisRequestId.current += 1;

      // 지도에 그려진 공역 경계 제거
      polygonsRef.current.forEach((polygon) => {
        polygon.setMap(null);
      });

      polygonsRef.current = [];

      // 열려 있는 정보창 닫기
      if (infoWindowRef.current) {
        infoWindowRef.current.close();
        infoWindowRef.current = null;
      }

      // 분석 결과 제거
      setAirspaceResult(null);
      setAirspaceError(null);
    }
  }, [activeLayers]);

  return (
    <section>
      <div className="map-header">
        <div className="info-panels">
          {activeLayers.map((layerId) => {
            const layer = LAYERS.find((item) => item.id === layerId);
            return (
              <InfoBox key={layerId} title={layer ? layer.label : layerId}>
                임시내용
              </InfoBox>
            );
          })}
        </div>
        <DroneSelect
          options={drones}
          value={selectedDroneId}
          onChange={setSelectedDroneId}
        />
      </div>
      {/* <p>선택한 기종 : {selectedDroneId}</p> */}

      <div className="map-box">
        <div className="layer-toggle">
          {LAYERS.map((layer) => (
            <button
              className={
                activeLayers.includes(layer.id)
                  ? "layer-btn layer-btn--on"
                  : "layer-btn"
              }
              aria-pressed={activeLayers.includes(layer.id)}
              onClick={() => toggleLayer(layer.id)}
              key={layer.id}
              title={layer.label}
              type="button"
            >
              {layer.icon}
            </button>
          ))}
        </div>
        <div id="kakao-map" style={{ width: "100%", height: "100%" }} />
      </div>

      {airspaceError && <p style={{ color: "red" }}>⚠️ {airspaceError}</p>}

      {airspaceResult && (
        <div>
          <h3>
            {airspaceResult.status === "PROHIBITED_AIRSPACE"
              ? "🚫 비행금지구역"
              : airspaceResult.status === "RESTRICTED_AIRSPACE"
                ? "⚠️ 비행제한구역"
                : "🔎 추가 확인 필요"}
          </h3>

          <p>{airspaceResult.message}</p>
          <p>조회된 공역: {airspaceResult.airspace_count}개</p>
          <small>
            이 결과는 P/R 공역 기준 참고 정보이며, 실제 비행 가능 여부와 승인
            요건은 별도로 확인해야 합니다.
          </small>
        </div>
      )}
    </section>
  );
}

export default function MapPage() {
  const { mode } = useParams();

  if (!mode || !MODES.includes(mode)) {
    return <Navigate to="/" replace />;
  }
  return <MapView mode={mode} key={mode} />;
}

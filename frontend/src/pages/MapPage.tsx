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

  const [selectedDrone, setSelectedDrone] = useState("");
  const [flightResult, setFlightResult] = useState<any>(null);
  const [flightLoading, setFlightLoading] = useState(false);
  const [flightError, setFlightError] = useState("");
  const [activeLayers, setActiveLayers] = useState<string[]>(
    mode ? [mode] : [],
  );
  const [drones, setDrones] = useState<DroneModel[]>([]);

  const [selectedLocation, setSelectedLocation] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);

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

          if (
            !activeLayersRef.current.includes("restricted") &&
            !activeLayersRef.current.includes("suitability")
          ) {
            return;
          }
          const latlng = mouseEvent.latLng;

          const latitude = latlng.getLat();
          const longitude = latlng.getLng();
          setSelectedLocation({ latitude, longitude });

          if (!activeLayersRef.current.includes("restricted")) {
            return;
          }

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


  function getResultInfo(status: string) {
    switch (status) {
      case "GOOD":
        return { text: "양호", color: "#16a34a", icon: "🟢" };
      case "CAUTION":
        return { text: "주의", color: "#f59e0b", icon: "🟠" };
      case "NOT_RECOMMENDED":
        return { text: "비행 비권장", color: "#dc2626", icon: "🔴" };
      default:
        return { text: "판단 불가", color: "#6b7280", icon: "⚪" };
    }
  }

  async function analyzeFlight() {
    if (!selectedDrone) {
      setFlightError("드론을 먼저 선택해주세요.");
      return;
    }
    if (!selectedLocation) {
      setFlightError("지도에서 분석할 위치를 먼저 클릭해주세요.");
      return;
    }

    setFlightLoading(true);
    setFlightError("");
    setFlightResult(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/flight-analysis?model_id=${encodeURIComponent(selectedDrone)}&latitude=${selectedLocation.latitude}&longitude=${selectedLocation.longitude}`
      );

      if (!response.ok) {
        throw new Error("분석 요청 실패");
      }

      const data = await response.json();
      setFlightResult(data);
    } catch (error) {
      console.error(error);
      setFlightError("비행 적합도 분석에 실패했습니다.");
    } finally {
      setFlightLoading(false);
    }
  }

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
          value={selectedDrone}
          onChange={setSelectedDrone}
        />
      </div>
      {/* <p>선택한 기종 : {selectedDrone}</p> */}


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

      <p>켜진 레이어: {activeLayers.join(", ")}</p>
      {
        activeLayers.includes("suitability") && (
          <div style={{ padding: "20px", border: "1px solid #ddd" }}>
            <h3>드론 비행 적합도 분석</h3>

            <label htmlFor="drone-select">드론 선택: </label>

            <select
              id="drone-select"
              value={selectedDrone}
              onChange={(e) => {
                setSelectedDrone(e.target.value);
                setFlightResult(null);
                setFlightError("");
              }}
            >
              <option value="">드론을 선택하세요</option>

              {drones.map((drone) => (
                <option key={drone.id} value={drone.id}>
                  {drone.name}
                </option>
              ))}
            </select>

            <p>
              {selectedLocation
                ? `선택한 위치: 위도 ${selectedLocation.latitude.toFixed(4)}, 경도 ${selectedLocation.longitude.toFixed(4)}`
                : "지도에서 분석할 위치를 클릭해주세요."}
            </p>
            <button
              type="button"
              onClick={analyzeFlight}
              disabled={flightLoading || !selectedDrone}
            >
              {flightLoading ? "분석 중..." : "비행 적합도 분석"}
            </button>

            {flightError && <p style={{ color: "red" }}>{flightError}</p>}

            {flightResult && (
              <div style={{ marginTop: "20px" }}>
                <h3>분석 결과</h3>

                <p>드론: {flightResult.drone}</p>
                <p>예보 시간: {flightResult.forecast_at}</p>
                <p>
                  풍속: {flightResult.wind_speed} m/s
                  (드론 기준: {flightResult.max_wind} m/s)
                </p>

                <p>
                  기온: {flightResult.temperature}°C
                  (작동 온도: {flightResult.min_temp}°C ~ {flightResult.max_temp}°C)
                </p>
                <p>
                  풍속 평가:{" "}
                  <span style={{ color: getResultInfo(flightResult.wind_result).color }}>
                    {getResultInfo(flightResult.wind_result).icon}{" "}
                    {getResultInfo(flightResult.wind_result).text}
                  </span>
                </p>
                <p style={{ fontSize: "14px", color: "#666" }}>
                  {flightResult.wind_result === "GOOD"
                    ? "현재 풍속이 드론 풍속 기준의 50% 미만으로 양호합니다."
                    : flightResult.wind_result === "CAUTION"
                      ? "현재 풍속이 드론 풍속 기준의 50~70% 구간으로 주의가 필요합니다."
                      : flightResult.wind_result === "NOT_RECOMMENDED"
                        ? "현재 풍속이 드론 풍속 기준의 70% 이상으로 비행을 권장하지 않습니다."
                        : "풍속 정보를 확인할 수 없습니다."}
                </p>

                <p>
                  기온 평가:{" "}
                  <span style={{ color: getResultInfo(flightResult.temperature_result).color }}>
                    {getResultInfo(flightResult.temperature_result).icon}{" "}
                    {getResultInfo(flightResult.temperature_result).text}
                  </span>
                </p>
                <p style={{ fontSize: "14px", color: "#666" }}>
                  {flightResult.temperature_result === "GOOD"
                    ? "현재 기온이 드론의 작동 온도 범위 내에 있어 양호합니다."
                    : flightResult.temperature_result === "CAUTION"
                      ? "현재 기온이 0°C 이하이거나 드론 작동 온도의 경계에 가까워 주의가 필요합니다."
                      : flightResult.temperature_result === "NOT_RECOMMENDED"
                        ? "현재 기온이 드론의 작동 온도 범위를 벗어나 비행을 권장하지 않습니다."
                        : "기온 정보를 확인할 수 없습니다."}
                </p>

                <p>
                  강수 평가:{" "}
                  <span style={{ color: getResultInfo(flightResult.precipitation_result).color }}>
                    {getResultInfo(flightResult.precipitation_result).icon}{" "}
                    {getResultInfo(flightResult.precipitation_result).text}
                  </span>
                </p>
                <p style={{ fontSize: "14px", color: "#666" }}>
                  {flightResult.precipitation_result === "UNKNOWN"
                    ? "강수 데이터가 아직 검증되지 않아 비나 눈이 오는지 판단할 수 없습니다."
                    : flightResult.precipitation_result === "NOT_RECOMMENDED"
                      ? "비 또는 눈이 예상되어 비행을 권장하지 않습니다."
                      : flightResult.precipitation_result === "GOOD"
                        ? "강수 조건이 양호합니다."
                        : "강수 조건에 주의가 필요합니다."}
                </p>

                <h2>
                  최종 결과:{" "}
                  <span
                    style={{
                      color: getResultInfo(flightResult.final_result).color,
                      fontWeight: "bold",
                    }}
                  >
                    {getResultInfo(flightResult.final_result).icon}{" "}
                    {getResultInfo(flightResult.final_result).text}
                  </span>
                </h2>

                <small>
                  현재는 임시 격자 기준의 기상 적합도이며, 실제 비행 가능 여부는
                  공역 및 승인 요건을 별도로 확인해야 합니다.
                </small>
              </div>
            )}
          </div>
        )
      }


      {airspaceError && <p style={{ color: "red" }}>⚠️ {airspaceError}</p>}

      {
        airspaceResult && (
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
        )
      }
    </section >
  );
}

export default function MapPage() {
  const { mode } = useParams();

  if (!mode || !MODES.includes(mode)) {
    return <Navigate to="/" replace />;
  }
  return <MapView mode={mode} key={mode} />;
}

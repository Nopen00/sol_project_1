import { Navigate, useParams } from "react-router-dom";
import "./MapPage.css";
import { useEffect, useState } from "react";
import { fetchDrones, fetchFlightAnalysis } from "../api/map";
import { useKakaoMap } from "../features/map/useKakaoMap";
import type { DroneOption, FlightAnalysisResult } from "../types/map";

const MODES = ["restricted", "weather", "suitability"];
const LAYERS = [
  { id: "restricted", label: "비행제한구역", icon: "🚫" },
  { id: "weather", label: "날씨", icon: "☀️" },
  { id: "suitability", label: "비행 적합도", icon: "📊" },
  { id: "grid", label: "격자 on/off", icon: "🏁" },
];

export function MapView({ mode }: { mode: string }) {
  const [drones, setDrones] = useState<DroneOption[]>([]);

  const [selectedDrone, setSelectedDrone] = useState("");
  const [flightResult, setFlightResult] = useState<FlightAnalysisResult | null>(null);
  const [flightLoading, setFlightLoading] = useState(false);
  const [flightError, setFlightError] = useState("");
  
  const [activeLayers, setActiveLayers] = useState<string[]>(() => {
  const params = new URLSearchParams(window.location.search);

  const fromMain =
    params.has("lat") && params.has("lng");

  // 메인 페이지에서 지역 좌표를 전달한 경우
  if (fromMain) {
    return ["restricted", "weather"];
  }

  // 일반적인 지도 페이지 진입
  return mode ? [mode] : [];
});

  const { selectedLocation, airspaceResult, airspaceError, weatherResult, weatherError, weatherLoading } = useKakaoMap(activeLayers);

  const toggleLayer = (id: string) => {
    setActiveLayers((previous) => previous.includes(id)
      ? previous.filter((layerId) => layerId !== id)
      : [...previous, id]);
  };

  useEffect(() => {
    fetchDrones()
      .then(setDrones)
      .catch((error) => console.error("드론 목록 불러오기 실패:", error));
  }, []);

  function getResultInfo(status: string) {
    switch (status) {
      case "GOOD":
        return { text: "양호", className: "analysis-status--good", icon: "🟢" };
      case "CAUTION":
        return { text: "주의", className: "analysis-status--caution", icon: "🟠" };
      case "NOT_RECOMMENDED":
        return { text: "비행 비권장", className: "analysis-status--not-recommended", icon: "🔴" };
      default:
        return { text: "판단 불가", className: "analysis-status--unknown", icon: "⚪" };
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
      const data = await fetchFlightAnalysis(selectedDrone, selectedLocation.latitude, selectedLocation.longitude);
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
      <h1>{mode} 지도</h1>


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
        <div
          id="kakao-map"
          style={{ width: "100%", height: "500px" }}
        />
      </div>
      <p>켜진 레이어: {activeLayers.join(", ")}</p>
      {activeLayers.includes("suitability") && (
        <div className="analysis-panel">
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

          {flightError && <p className="analysis-error">{flightError}</p>}

          {flightResult && (
            <div className="analysis-result">
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
                <span className={getResultInfo(flightResult.wind_result).className}>
                  {getResultInfo(flightResult.wind_result).icon}{" "}
                  {getResultInfo(flightResult.wind_result).text}
                </span>
              </p>
              <p className="analysis-explanation">
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
                <span className={getResultInfo(flightResult.temperature_result).className}>
                  {getResultInfo(flightResult.temperature_result).icon}{" "}
                  {getResultInfo(flightResult.temperature_result).text}
                </span>
              </p>
              <p className="analysis-explanation">
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
                <span className={getResultInfo(flightResult.precipitation_result).className}>
                  {getResultInfo(flightResult.precipitation_result).icon}{" "}
                  {getResultInfo(flightResult.precipitation_result).text}
                </span>
              </p>
              <p className="analysis-explanation">
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
                  className={`${getResultInfo(flightResult.final_result).className} analysis-final`}
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
      )}

      {activeLayers.includes("weather") && (
        <section className="map-weather-panel" aria-live="polite">
          <h3>선택 지역 날씨 정보</h3>
          {selectedLocation && (
            <p>조회 좌표: {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}</p>
          )}
          {!selectedLocation && <p>지도에서 위치를 클릭하거나 메인페이지에서 지역을 선택하세요.</p>}
          {weatherLoading && <p>날씨 예보 조회 중...</p>}
          {weatherError && <p className="analysis-error">{weatherError}</p>}
          {selectedLocation && !weatherLoading && !weatherError && !weatherResult && (
            <p>표시할 날씨 데이터가 없습니다. 백엔드 /weather/point 응답을 확인하세요.</p>
          )}
          {weatherResult && !weatherLoading && (
            <div>
              <p>예보 시간: {weatherResult.forecast_at ?? "정보 없음"}</p>
              <p>기온: {weatherResult.temperature ?? "정보 없음"}°C</p>
              <p>풍속: {weatherResult.wind_speed ?? "정보 없음"} m/s</p>
              <p>강수: {weatherResult.precipitation ?? "정보 없음"}</p>
              <p>강수 형태: {weatherResult.precipitation_type_status ?? weatherResult.precipitation_type ?? "정보 없음"}</p>
              <small>Oracle DB의 해당 격자 예보를 표시합니다. 지도 색상형 기상 위험도는 별도 기능입니다.</small>
            </div>
          )}
        </section>
      )}

      {airspaceError && (
        <p className="analysis-error">
          ⚠️ {airspaceError}
        </p>
      )}

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
            이 결과는 P/R 공역 기준 참고 정보이며,
            실제 비행 가능 여부와 승인 요건은 별도로 확인해야 합니다.
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

import { Navigate, useParams } from "react-router-dom";
import "./MapPage.css";
import { useState } from "react";

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
  const toggleLayer = (id: string) => {
    if (activeLayers.includes(id)) {
      setActiveLayers(activeLayers.filter((layerId) => layerId !== id)); // 빼기: 그 id만 빠진 새 배열
    } else {
      setActiveLayers([...activeLayers, id]); // 넣기: 기존 + 그 id 가 있는 새 배열
    }
  };

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
        지도가 들어갈 자리
      </div>
      <p>켜진 레이어: {activeLayers.join(", ")}</p>
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

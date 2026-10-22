import { useState } from "react";
import InfoBox from "../../components/InfoBox";

interface MapScreenProps {
  mode: string;
}

const LAYERS = [
  { id: "restricted", label: "비행 제한 구역", icon: "🚫" },
  { id: "weather", label: "날씨", icon: "☀️" },
  { id: "suitability", label: "비행 적합도", icon: "📊" },
  { id: "grid", label: "격자 on/off", icon: "🏁" },
];

export const MapScreen = ({ mode }: MapScreenProps) => {
  const [activeLayerIds, setActiveLayerIds] = useState<string[]>([mode]);

  const handleLayerToggle = (layerId: string) => {
    if (activeLayerIds.includes(layerId)) {
      setActiveLayerIds(activeLayerIds.filter((id) => id !== layerId));
    } else {
      setActiveLayerIds([...activeLayerIds, layerId]);
    }
  };

  return (
    <section>
      <h2>{mode} 지도</h2>
      <div>
        {activeLayerIds.map((layerId) => {
          const layer = LAYERS.find((item) => item.id === layerId);
          return (
            <InfoBox key={layerId} title={layer ? layer.label : layerId}>
              임시 내용
            </InfoBox>
          );
        })}
      </div>
      <div>
        {LAYERS.map((layer) => (
          <button
            type="button"
            title={layer.label}
            key={layer.id}
            onClick={() => {
              handleLayerToggle(layer.id);
            }}
          >
            {layer.icon}
          </button>
        ))}
      </div>
      <div style={{ height: "70vh" }}>지도가 들어갈 자리</div>
    </section>
  );
};

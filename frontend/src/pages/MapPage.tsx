import { Navigate, useParams } from "react-router-dom";
import { MapScreen } from "../features/map/MapScreen";

const MAP_MODES = ["restricted", "weather", "suitability"];

export const MapPage = () => {
  const { mode } = useParams();

  if (!mode || !MAP_MODES.includes(mode)) {
    return <Navigate to={"/"} replace />;
  }
  return <MapScreen mode={mode} key={mode} />;
};

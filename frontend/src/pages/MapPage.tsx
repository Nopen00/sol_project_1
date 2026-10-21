import { Navigate, useParams } from "react-router-dom";
import { MapScreen } from "../features/map/MapScreen";

const Map_Modes = ["restricted", "weather", "suitability"];

export const MapPage = () => {
  const { mode } = useParams();

  if (!mode || !Map_Modes.includes(mode)) {
    return <Navigate to={"/"} replace />;
  }
  return <MapScreen mode={mode} key={mode} />;
};

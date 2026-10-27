import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ComingSoon from "./components/ComingSoon";
import Main from "./pages/Main";
import MapPage from "./pages/MapPage";
import DroneInfo from "./pages/DroneInfo";
// import FlightAnalysis from "./pages/FlightAnalysis";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Main />} />

          {/* 지도 페이지 */}
          <Route path="/map" element={<MapPage />} />
          <Route path="/map/:mode" element={<MapPage />} />

          {/* 드론 정보 페이지 */}
          <Route path="/drone-info" element={<DroneInfo />} />

          {/* 비행 분석 페이지 */}
          {/* <Route path="/flight-analysis" element={<FlightAnalysis />} /> */}

          {/* 아직 없는 페이지 */}
          <Route path="*" element={<ComingSoon />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
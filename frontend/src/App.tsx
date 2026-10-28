import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./features/auth/AuthContext";
import Layout from "./components/Layout";
import ComingSoon from "./components/ComingSoon";
import Main from "./pages/Main";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import MapPage from "./pages/MapPage";
import Board from "./pages/Board";
// import DroneInfo from "./pages/DroneInfo";
// import FlightAnalysis from "./pages/FlightAnlaysis";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Main />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/map/:mode" element={<MapPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            {/* <Route path="/drone-info" element={<DroneInfo />} /> */}
            {/* 아직 없는 페이지는 임시 화면으로 연결. 페이지를 만들면 위에 Route를 추가한다. */}
            {/* <Route path="/drone-info" element={<DroneInfo />} />
            <Route path="/flight-analysis" element={<FlightAnalysis />} /> */}
            {/* 아직 없는 페이지 */}
            <Route path="*" element={<ComingSoon />} />
           <Route path="/board" element={<Board/>} />  {/*게시판*/}
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

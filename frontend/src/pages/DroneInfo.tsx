import DroneSelector from "../components/DroneSelector";
import "./DroneInfo.css";

export default function DroneInfo() {
    return (
        <section className="drone-page">
            <div className="drone-page-header">
                <h1>드론 정보</h1>
                <p>드론 기종을 선택하면 성능 정보를 확인할 수 있습니다.</p>
            </div>

            <DroneSelector />
        </section>
    );
}
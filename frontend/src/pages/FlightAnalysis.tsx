import { useState } from "react";

type FlightResult = {
    drone: string;
    forecast_at: string;
    wind_speed: number;
    temperature: number;
    wind_result: string;
    temperature_result: string;
    precipitation_result: string;
    final_result: string;
};

export default function FlightAnalysis() {
    const [result, setResult] = useState<FlightResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function analyze() {
        setLoading(true);
        setError("");

        try {
            const response = await fetch(
                "http://127.0.0.1:8001/flight-analysis?model_id=AUTEL_EVO_LITE&nx=60&ny=127"
            );

            if (!response.ok) {
                throw new Error("비행 적합도 조회 실패");
            }

            const data: FlightResult = await response.json();
            setResult(data);
        } catch {
            setError("서버 연결 또는 데이터 조회에 실패했습니다.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div style={{ padding: "30px" }}>
            <h2>드론 비행 적합도 분석</h2>

            <button onClick={analyze} disabled={loading}>
                {loading ? "분석 중..." : "비행 적합도 분석"}
            </button>

            {error && <p>{error}</p>}

            {result && (
                <div>
                    <h3>분석 결과</h3>
                    <p>드론: {result.drone}</p>
                    <p>예보 시간: {result.forecast_at}</p>
                    <p>풍속: {result.wind_speed}m/s</p>
                    <p>기온: {result.temperature}°C</p>
                    <p>풍속 평가: {result.wind_result}</p>
                    <p>기온 평가: {result.temperature_result}</p>
                    <p>강수 평가: {result.precipitation_result}</p>
                    <h3>최종 결과: {result.final_result}</h3>
                </div>
            )}
        </div>
    );
}
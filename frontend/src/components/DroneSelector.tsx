import { useEffect, useState } from "react";
import "./DroneSelector.css";

type Drone = {
    id: string;
    name: string;
    wind: number;
    minTemp: number;
    maxTemp: number;
};

export default function DroneSelector() {
    const [drones, setDrones] = useState<Drone[]>([]);
    const [selectedName, setSelectedName] = useState("");
    const [search, setSearch] = useState("");
    const [isOpen, setIsOpen] = useState(false);

    // 사용자가 입력한 현재 풍속
    const [currentWind, setCurrentWind] = useState<string>("");

    // 사용자가 입력한 현재 기온
    const [currentTemp, setCurrentTemp] = useState<string>("");

    useEffect(() => {
        fetch("http://127.0.0.1:8000/drones")
            .then((response) => {
                if (!response.ok) {
                    throw new Error("드론 데이터 조회 실패");
                }
                return response.json();
            })
            .then((data: Drone[]) => {
                setDrones(data);
            })
            .catch((error) => {
                console.error("드론 데이터 오류:", error);
            });
    }, []);

    const selectedDrone = drones.find(
        (drone) => drone.name === selectedName
    );

    const filteredDrones = drones.filter((drone) =>
        drone.name.toLowerCase().includes(search.toLowerCase())
    );

    const handleSelect = (name: string) => {
        setSelectedName(name);
        setSearch(name);
        setIsOpen(false);
    };

    return (
        <div className="drone-container">
            <div className="drone-card">
                <h3>드론 기종 선택</h3>

                <div style={{ position: "relative", width: "100%" }}>
                    <div style={{ display: "flex" }}>
                        <input
                            type="text"
                            placeholder="드론 기종 선택 또는 검색"
                            value={search}
                            onFocus={() => setIsOpen(true)}
                            onChange={(e) => {
                                setSearch(e.target.value);
                                setSelectedName("");
                                setIsOpen(true);
                            }}
                            aria-label="드론 기종 검색"
                            aria-expanded={isOpen}
                            aria-controls="drone-options"
                            style={{
                                width: "100%",
                                padding: "10px",
                                boxSizing: "border-box",
                            }}
                        />

                        <button
                            type="button"
                            onClick={() => setIsOpen(!isOpen)}
                            aria-label="드론 목록 열기 또는 닫기"
                        >
                            ▼
                        </button>
                    </div>

                    {isOpen && (
                        <div
                            id="drone-options"
                            style={{
                                position: "absolute",
                                top: "100%",
                                left: 0,
                                width: "100%",
                                maxHeight: "220px",
                                overflowY: "auto",
                                backgroundColor: "white",
                                border: "1px solid #ccc",
                                boxSizing: "border-box",
                                zIndex: 10,
                            }}
                        >
                            {filteredDrones.length > 0 ? (
                                filteredDrones.map((drone) => (
                                    <button
                                        key={drone.name}
                                        type="button"
                                        onClick={() => handleSelect(drone.name)}
                                        style={{
                                            display: "block",
                                            width: "100%",
                                            padding: "10px",
                                            textAlign: "left",
                                            backgroundColor: "white",
                                            color: "#111",
                                            border: "none",
                                            cursor: "pointer",
                                        }}
                                    >
                                        {drone.name}
                                    </button>
                                ))
                            ) : (
                                <p style={{ padding: "10px" }}>
                                    검색 결과가 없습니다.
                                </p>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {selectedDrone && (
                <div className="drone-card">
                    <h3>{selectedDrone.name}</h3>

                    <div className="drone-spec">
                        <div className="drone-spec-item">
                            <p>최대 내풍속</p>
                            <strong>{selectedDrone.wind} m/s</strong>
                        </div>

                        <div className="drone-spec-item">
                            <p>작동 온도</p>
                            <strong>
                                {selectedDrone.minTemp}°C ~ {selectedDrone.maxTemp}°C
                            </strong>
                        </div>

                        <div className="drone-spec-item">
                            <p>주의 시작</p>
                            <strong>
                                {(selectedDrone.wind * 0.5).toFixed(2)} m/s
                            </strong>
                        </div>

                        <div className="drone-spec-item">
                            <p>비권장 시작</p>
                            <strong>
                                {(selectedDrone.wind * 0.7).toFixed(2)} m/s
                            </strong>
                        </div>
                    </div>
                </div>
            )
            }
            {
                selectedDrone && (
                    <div className="drone-card">
                        <h3>현재 기상 조건 입력</h3>

                        <div className="drone-spec">
                            <div>
                                <label htmlFor="current-wind">현재 풍속 (m/s)</label>
                                <input
                                    id="current-wind"
                                    className="drone-input"
                                    type="number"
                                    min="0"
                                    placeholder="예: 5"
                                    value={currentWind}
                                    onChange={(e) => setCurrentWind(e.target.value)}
                                />
                            </div>

                            <div>
                                <label htmlFor="current-temp">현재 기온 (°C)</label>
                                <input
                                    id="current-temp"
                                    className="drone-input"
                                    type="number"
                                    placeholder="예: 25"
                                    value={currentTemp}
                                    onChange={(e) => setCurrentTemp(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>
                )
            }
            {
                selectedDrone && (
                    <div className="drone-card">
                        <h3>기상 조건 분석 결과</h3>

                        <div className="drone-spec">
                            <div className={`drone-result ${currentWind === ""
                                ? "result-waiting"
                                : Number(currentWind) < 0
                                    ? "result-danger"
                                    : Number(currentWind) <= selectedDrone.wind
                                        ? "result-success"
                                        : "result-danger"
                                }`}>
                                <h4>풍속 분석</h4>
                                <p>
                                    {currentWind === ""
                                        ? "풍속을 입력해 주세요"
                                        : Number(currentWind) < 0
                                            ? "올바른 풍속을 입력해 주세요"
                                            : Number(currentWind) <= selectedDrone.wind
                                                ? "풍속 조건 충족"
                                                : "풍속 조건 초과"}
                                </p>
                            </div>

                            <div className={`drone-result ${currentTemp === ""
                                ? "result-waiting"
                                : Number(currentTemp) >= selectedDrone.minTemp &&
                                    Number(currentTemp) <= selectedDrone.maxTemp
                                    ? "result-success"
                                    : "result-danger"
                                }`}>
                                <h4>온도 분석</h4>
                                <p>
                                    {currentTemp === ""
                                        ? "온도를 입력해 주세요"
                                        : Number(currentTemp) >= selectedDrone.minTemp &&
                                            Number(currentTemp) <= selectedDrone.maxTemp
                                            ? "온도 조건 충족"
                                            : "온도 조건 미충족"}
                                </p>
                            </div>
                        </div>
                    </div>
                )
            }
            {
                selectedDrone && (
                    <div className="drone-card">
                        <h3>종합 분석 결과</h3>
                        <p className={`drone-result ${currentWind === "" || currentTemp === ""
                            ? "result-waiting"
                            : Number(currentWind) >= 0 &&
                                Number(currentWind) <= selectedDrone.wind &&
                                Number(currentTemp) >= selectedDrone.minTemp &&
                                Number(currentTemp) <= selectedDrone.maxTemp
                                ? "result-success"
                                : "result-danger"
                            }`}>
                            {currentWind === "" || currentTemp === ""
                                ? "풍속과 온도를 모두 입력해 주세요"
                                : Number(currentWind) < 0
                                    ? "올바른 풍속을 입력해 주세요"
                                    : Number(currentWind) <= selectedDrone.wind &&
                                        Number(currentTemp) >= selectedDrone.minTemp &&
                                        Number(currentTemp) <= selectedDrone.maxTemp
                                        ? "풍속과 온도 조건 모두 충족"
                                        : "풍속 또는 온도 조건 미충족"}
                        </p>
                    </div>
                )
            }
        </div >
    )
}
import { useState, useEffect } from "react";

type Drone = {
    id: string;
    name: string;
    wind: number;
    minTemp: number;
    maxTemp: number;
}

function App() {
    // 1. DB에서 가져올 드론 목록
    const [drones, setDrones] = useState<Drone[]>([]);

    // 2. 사용자가 선택한 드론 
    const [selectedDrone, setSelectedDrone] = useState<Drone | null>(null);

    // 3. 사용자가 입력한 풍속
    const [currentWind, setCurrentWind] = useState<string>("");

    // 4. 사용자가 입력한 온도
    const [currentTemp, setCurrentTemp] = useState<string>("");

    useEffect(() => {
        fetch("http://127.0.0.1:8000/drones")
            .then((response) => response.json())
            .then((data) => {
                setDrones(data)
            });
    }, []);

    return (
        <div>
            <h1>드론 비행 지도</h1>
            {drones.map((drone) => (
                <button key={drone.id}
                    onClick={() => setSelectedDrone(drone)}
                >
                    {drone.name}
                </button>
            ))}
            {selectedDrone && (
                <div>
                    <h2>선택한 드론</h2>
                    <p>드론 이름: {selectedDrone.name}</p>
                    <p>최대 풍속 저항: {selectedDrone.wind}m/s</p>
                    <p>최저 작동 온도: {selectedDrone.minTemp}°C</p>
                    <p>최고 작동 온도: {selectedDrone.maxTemp}°C</p>
                </div>
            )}
            <div>
                <h3>현재 풍속 입력</h3>
                <input
                    type="number"
                    value={currentWind}
                    onChange={(e) => setCurrentWind(e.target.value)}
                />
                <span> m/s </span>
            </div>
            {selectedDrone && (
                <div>
                    <h3>풍속 분석 결과</h3>
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
            )}
            <div>
                <h3>현재 기온 입력</h3>
                <input
                    type="number"
                    value={currentTemp}
                    onChange={(e) => setCurrentTemp(e.target.value)}
                />
                <span>°C</span>
            </div>
            {selectedDrone && (
                <div>
                    <h3>온도 분석 결과</h3>
                    <p>
                        {currentTemp === ""
                            ? "온도을 입력해 주세요"
                            : Number(currentTemp) <= selectedDrone.maxTemp &&
                                Number(currentTemp) >= selectedDrone.minTemp
                                ? "온도 조건 충족"
                                : "온도 조건 미충족"}
                    </p>
                </div>
            )}
            {selectedDrone && (
                <div>
                    <h3>종합 분석 결과</h3>
                    <p>
                        {currentWind !== "" &&
                            currentTemp !== "" &&
                            Number(currentWind) >= 0 &&
                            Number(currentWind) <= selectedDrone.wind &&
                            Number(currentTemp) >= selectedDrone.minTemp &&
                            Number(currentTemp) <= selectedDrone.maxTemp
                        }
                    </p>
                </div>
            )}

        </div>
    )
};

export default App;
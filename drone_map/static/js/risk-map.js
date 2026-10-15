
const RISK_COLORS = {
    1: "#facc15",
    2: "#f97316",
    3: "#ef4444"
};

// 기존 함수명과의 호환성을 위해 유지
function clearRiskCircles() {
    if (typeof currentRiskZones !== "undefined") {
        currentRiskZones = [];
    }
}

// 위험 구역을 별도로 그리지 않고
// 일반 격자에 위험 색상을 통합 적용
function drawRiskZones(map, zones, infoWindow) {
    updateGridRiskZones(
        map,
        zones || [],
        infoWindow
    );
}

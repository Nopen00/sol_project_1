
const MAP_GRID_STEP = 0.001;
const MAX_MAP_GRIDS = 3000;

const GRID_RISK_COLORS = {
    0: "#ffffff",
    1: "#facc15",
    2: "#f97316",
    3: "#ef4444"
};

let mapGridRectangles = [];
let currentGridCells = [];
let currentRiskZones = [];
let currentGridMap = null;
let currentGridInfoWindow = null;

// 격자 개수 계산
function countMergedGrids(bounds, mergeSize) {
    const step = MAP_GRID_STEP * mergeSize;
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();

    const latStart = Math.floor(sw.getLat() / step);
    const latEnd = Math.ceil(ne.getLat() / step);
    const lonStart = Math.floor(sw.getLng() / step);
    const lonEnd = Math.ceil(ne.getLng() / step);

    return (latEnd - latStart) * (lonEnd - lonStart);
}

// 최대 3,000개를 만족하는 홀수 병합 크기
function getMergeSize(map) {
    const bounds = map.getBounds();
    let mergeSize = 1;

    while (
        countMergedGrids(bounds, mergeSize) >
        MAX_MAP_GRIDS
    ) {
        mergeSize += 2;
    }

    return mergeSize;
}

function getMapGridCount(map) {
    return countMergedGrids(
        map.getBounds(),
        getMergeSize(map)
    );
}

function clearMapGrids() {
    mapGridRectangles.forEach(rectangle => {
        rectangle.setMap(null);
    });

    mapGridRectangles = [];
    currentGridCells = [];
}

// 서버가 제공하는 기상청 격자 중심의
// 대략적인 영향 범위와 표시 격자의 겹침 확인
function intersectsRiskZone(cell, zone) {
    const radius = zone.radius || 2500;

    const latRadius = radius / 111320;
    const lonRadius =
        radius /
        (111320 * Math.cos(zone.lat * Math.PI / 180));

    const zoneSouth = zone.lat - latRadius;
    const zoneNorth = zone.lat + latRadius;
    const zoneWest = zone.lon - lonRadius;
    const zoneEast = zone.lon + lonRadius;

    return (
        cell.south <= zoneNorth &&
        cell.north >= zoneSouth &&
        cell.west <= zoneEast &&
        cell.east >= zoneWest
    );
}

// 병합 격자와 겹치는 위험 구역 중
// 가장 높은 위험 등급 선택
function getCellRisk(cell, zones) {
    let highestLevel = 0;
    let highestZone = null;

    for (const zone of zones) {
        if (!intersectsRiskZone(cell, zone)) {
            continue;
        }

        const level = Number(zone.risk?.level ?? 0);

        if (level > highestLevel) {
            highestLevel = level;
            highestZone = zone;
        }
    }

    return {
        level: highestLevel,
        zone: highestZone
    };
}

// 지도 전체 격자 생성
function drawMapGrids(
    map,
    zones = currentRiskZones,
    infoWindow = currentGridInfoWindow
) {
    currentGridMap = map;
    currentRiskZones = zones;
    currentGridInfoWindow = infoWindow;

    const bounds = map.getBounds();
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();

    const mergeSize = getMergeSize(map);
    const step = MAP_GRID_STEP * mergeSize;

    const latStart = Math.floor(sw.getLat() / step);
    const latEnd = Math.ceil(ne.getLat() / step);
    const lonStart = Math.floor(sw.getLng() / step);
    const lonEnd = Math.ceil(ne.getLng() / step);

    clearMapGrids();

    for (let i = latStart; i < latEnd; i++) {
        for (let j = lonStart; j < lonEnd; j++) {

            const cell = {
                south: i * step,
                north: (i + 1) * step,
                west: j * step,
                east: (j + 1) * step
            };

            const risk = getCellRisk(cell, zones);
            const airspaces = typeof getCellAirspaces === "function" ? getCellAirspaces(cell) : [];
            const airspace = airspaces[0] || null;

            const rectangle = new kakao.maps.Rectangle({
                bounds: new kakao.maps.LatLngBounds(
                    new kakao.maps.LatLng(
                        cell.south,
                        cell.west
                    ),
                    new kakao.maps.LatLng(
                        cell.north,
                        cell.east
                    )
                ),
                strokeWeight: 1,
                strokeColor: "#64748b",
                strokeOpacity: 0.45,
                fillColor:
                    (airspace ? AIRSPACE_COLORS[airspace.type] : GRID_RISK_COLORS[risk.level]) ||
                    "#ffffff",
                fillOpacity: airspace
                    ? (map.getLevel() >= 10
                        ? (airspace.type === "prohibited" ? 0.55 : 0.23)
                        : (airspace.type === "prohibited" ? 0.8 : 0.45))
                    : (risk.level > 0 ? 0.5 : 0)
            });

            rectangle.setMap(map);

            if ((risk.zone || airspace) && infoWindow) {
                kakao.maps.event.addListener(
                    rectangle,
                    "click",
                    function (mouseEvent) {
                        const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
                        const props = airspace?.properties || {};
                        const name = props.name || props.NAME || props.designator || props.identifier || props.id || "공역";
                        const airspaceHtml = airspaces.length ? `<div style="padding:8px;max-height:180px;overflow:auto"><strong>겹치는 공역 ${airspaces.length}개 (격자 근사 표시)</strong>${airspaces.slice(0,15).map(item => `<div style="margin-top:5px">${escapeHtml(item.type === 'prohibited' ? '비행금지공역' : '비행제한·기타 공역')} · ${escapeHtml(item.category)} · ${escapeHtml(item.properties?.name || '이름 없음')}</div>`).join('')}${airspaces.length>15 ? `<div>외 ${airspaces.length-15}개</div>` : ''}</div>` : "";
                        const weatherHtml = risk.zone ? createWeatherInfo(risk.zone.weather, risk.zone.risk) : "";
                        infoWindow.setContent(airspaceHtml + weatherHtml);

                        infoWindow.setPosition(
                            mouseEvent.latLng
                        );

                        infoWindow.open(map);
                    }
                );
            }

            mapGridRectangles.push(rectangle);
            currentGridCells.push(cell);
        }
    }

    console.log(
        `병합 ${mergeSize}×${mergeSize}, ` +
        `표시 격자 ${mapGridRectangles.length}개`
    );

    return true;
}

// 새로운 위험 데이터 적용
function updateGridRiskZones(map, zones, infoWindow) {
    drawMapGrids(map, zones, infoWindow);
}

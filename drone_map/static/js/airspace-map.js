// GeoJSON 공역을 기존 지도 격자에 매핑합니다.
const AIRSPACE_COLORS = { prohibited: '#B91C1C', restricted: '#9333EA' };
let airspaceFeatures = [];

async function loadAirspaceZones(map) {
    const sources = [
        ['/static/data/prohibited_zones.geojson', 'prohibited'],
        ['/static/data/restricted_zones.geojson', 'restricted']
    ];
    const results = await Promise.all(sources.map(async ([url, type]) => {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`${response.status} ${url}`);
            const json = await response.json();
            const features = json.type === 'FeatureCollection' ? json.features : json.type === 'Feature' ? [json] : [{geometry: json, properties: {}}];
            return features.flatMap(feature => {
                const geom = feature.geometry;
                if (!geom || !['Polygon', 'MultiPolygon'].includes(geom.type)) return [];
                const polygons = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
                return polygons.map(rings => {
                    const outer = rings[0];
                    if (!outer?.length) return null;
                    return {type, rings, properties: feature.properties || {}, bbox: {
                        west: Math.min(...outer.map(p => p[0])), east: Math.max(...outer.map(p => p[0])),
                        south: Math.min(...outer.map(p => p[1])), north: Math.max(...outer.map(p => p[1]))
                    }};
                }).filter(Boolean);
            });
        } catch (error) {
            console.error('공역 GeoJSON 로드 실패:', error);
            return [];
        }
    }));
    airspaceFeatures = results.flat();
    if (typeof currentGridMap !== 'undefined' && currentGridMap) drawMapGrids(currentGridMap);
}

function pointInRing(point, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const a = ring[i], b = ring[j];
        if ((a[1] > point[1]) !== (b[1] > point[1]) &&
            point[0] < (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
    }
    return inside;
}
function pointInPolygon(point, rings) {
    return pointInRing(point, rings[0]) && !rings.slice(1).some(ring => pointInRing(point, ring));
}
function segmentsCross(a, b, c, d) {
    const cross = (p, q, r) => (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]);
    const on = (p,q,r) => Math.min(p[0],q[0]) <= r[0] && r[0] <= Math.max(p[0],q[0]) && Math.min(p[1],q[1]) <= r[1] && r[1] <= Math.max(p[1],q[1]);
    const x=cross(a,b,c), y=cross(a,b,d), z=cross(c,d,a), w=cross(c,d,b);
    return ((x>0&&y<0||x<0&&y>0)&&(z>0&&w<0||z<0&&w>0)) ||
        (x===0&&on(a,b,c))||(y===0&&on(a,b,d))||(z===0&&on(c,d,a))||(w===0&&on(c,d,b));
}
function intersectsAirspace(cell, feature) {
    const b = feature.bbox;
    if (cell.east < b.west || cell.west > b.east || cell.north < b.south || cell.south > b.north) return false;
    const corners = [[cell.west,cell.south],[cell.east,cell.south],[cell.east,cell.north],[cell.west,cell.north]];
    if (corners.some(p => pointInPolygon(p,feature.rings))) return true;
    if (feature.rings[0].some(p => p[0]>=cell.west&&p[0]<=cell.east&&p[1]>=cell.south&&p[1]<=cell.north)) return true;
    for (const ring of feature.rings) for (let i=0;i<ring.length;i++) {
        const a=ring[i], b=ring[(i+1)%ring.length];
        for (let j=0;j<4;j++) if (segmentsCross(a,b,corners[j],corners[(j+1)%4])) return true;
    }
    return false;
}
function getCellAirspace(cell) {
    let restricted = null;
    for (const feature of airspaceFeatures) {
        if (!intersectsAirspace(cell, feature)) continue;
        if (feature.type === 'prohibited') return feature;
        if (!restricted) restricted = feature;
    }
    return restricted;
}

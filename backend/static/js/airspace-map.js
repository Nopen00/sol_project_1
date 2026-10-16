// AIP 공역을 격자에 투영하는 시각화 모듈. 비행 허가 판정용이 아닙니다.
const AIRSPACE_COLORS = { prohibited: '#000000', restricted: '#9333EA' };
// 격자 채색은 드론 비행에 직접 관련된 P/R/관제권만 사용합니다.
const AIRSPACE_DATASETS = [
  ['prohibited', 'prohibited', '비행금지공역'],
  ['restricted', 'restricted', '비행제한공역'],
  ['control', 'restricted', '공항·비행장 관제권']
];
// 기타 고고도/항로 공역은 격자 및 지도 경계선에 표시하지 않습니다.
let airspaceFeatures = [];
let airspaceBuckets = new Map();
let airspaceVisibility = { prohibited: true, restricted: true };
let airspaceLoaded = false;
const BUCKET_STEP = 0.5;
const airspaceBucketKey = (x,y) => `${x}:${y}`;

async function loadAirspaceZones(map) {
  const results = await Promise.all(AIRSPACE_DATASETS.map(async ([file,type,category]) => {
    const url = `/static/data/airspace/${file}.geojson`;
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`${response.status} ${url}`);
      const json = await response.json();
      if (json.type !== 'FeatureCollection' || !Array.isArray(json.features)) throw new Error('잘못된 GeoJSON');
      return json.features.flatMap(feature => {
        const geometry = feature.geometry;
        if (!geometry || !['Polygon','MultiPolygon'].includes(geometry.type)) return [];
        const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
        return polygons.map(rings => {
          if (!rings?.[0]?.length) return null;
          const outer = rings[0];
          const xs = outer.map(p => p[0]), ys = outer.map(p => p[1]);
          return { type, category, rings, properties: feature.properties || {}, bbox: {
            west: Math.min(...xs), east: Math.max(...xs), south: Math.min(...ys), north: Math.max(...ys)
          }};
        }).filter(Boolean);
      });
    } catch (error) {
      console.error('공역 로드 실패:', error);
      return [];
    }
  }));
  airspaceFeatures = results.flat();
  airspaceBuckets = new Map();
  for (const feature of airspaceFeatures) {
    const b = feature.bbox;
    for (let x=Math.floor(b.west/BUCKET_STEP);x<=Math.floor(b.east/BUCKET_STEP);x++) {
      for (let y=Math.floor(b.south/BUCKET_STEP);y<=Math.floor(b.north/BUCKET_STEP);y++) {
        const key = airspaceBucketKey(x,y);
        if (!airspaceBuckets.has(key)) airspaceBuckets.set(key,[]);
        airspaceBuckets.get(key).push(feature);
      }
    }
  }
  airspaceLoaded = true;
  console.log(`공역 다각형 ${airspaceFeatures.length}개 로드 완료`);
  if (typeof currentGridMap !== 'undefined' && currentGridMap) drawMapGrids(currentGridMap);
  return airspaceFeatures.length;
}

function pointInRing(point, ring) {
  let inside = false;
  for (let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const a=ring[i],b=ring[j];
    if ((a[1]>point[1]) !== (b[1]>point[1]) && point[0] < (b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0]) inside=!inside;
  }
  return inside;
}
function pointInPolygon(point,rings) {
  return pointInRing(point,rings[0]) && !rings.slice(1).some(r=>pointInRing(point,r));
}
function segmentsCross(a,b,c,d) {
  const cross=(p,q,r)=>(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]);
  const on=(p,q,r)=>Math.min(p[0],q[0])-1e-10<=r[0]&&r[0]<=Math.max(p[0],q[0])+1e-10&&Math.min(p[1],q[1])-1e-10<=r[1]&&r[1]<=Math.max(p[1],q[1])+1e-10;
  const x=cross(a,b,c),y=cross(a,b,d),z=cross(c,d,a),w=cross(c,d,b);
  return (((x>0&&y<0)||(x<0&&y>0))&&((z>0&&w<0)||(z<0&&w>0))) ||
    (Math.abs(x)<1e-10&&on(a,b,c))||(Math.abs(y)<1e-10&&on(a,b,d))||(Math.abs(z)<1e-10&&on(c,d,a))||(Math.abs(w)<1e-10&&on(c,d,b));
}
function intersectsAirspace(cell,feature) {
  const b=feature.bbox;
  if(cell.east<b.west||cell.west>b.east||cell.north<b.south||cell.south>b.north) return false;
  const corners=[[cell.west,cell.south],[cell.east,cell.south],[cell.east,cell.north],[cell.west,cell.north]];
  if(corners.some(p=>pointInPolygon(p,feature.rings))) return true;
  // 외곽점이 격자 안에 있어도 구멍 안에 완전히 들어 있는 경우는 제외
  if(feature.rings[0].some(p=>p[0]>=cell.west&&p[0]<=cell.east&&p[1]>=cell.south&&p[1]<=cell.north)) return true;
  for(const ring of feature.rings) for(let i=0;i<ring.length;i++) {
    const a=ring[i],b=ring[(i+1)%ring.length];
    for(let j=0;j<4;j++) if(segmentsCross(a,b,corners[j],corners[(j+1)%4])) return true;
  }
  return false;
}
function getCellAirspaces(cell) {
  const candidates=new Set();
  for(let x=Math.floor(cell.west/BUCKET_STEP);x<=Math.floor(cell.east/BUCKET_STEP);x++) {
    for(let y=Math.floor(cell.south/BUCKET_STEP);y<=Math.floor(cell.north/BUCKET_STEP);y++) {
      for(const feature of airspaceBuckets.get(airspaceBucketKey(x,y))||[]) candidates.add(feature);
    }
  }
  const matches=[];
  for(const feature of candidates) {
    if(!airspaceVisibility[feature.type]) continue;
    if(intersectsAirspace(cell,feature)) matches.push(feature);
  }
  matches.sort((a,b)=>(a.type==='prohibited'?-1:1)-(b.type==='prohibited'?-1:1));
  return matches;
}
function getCellAirspace(cell) { return getCellAirspaces(cell)[0]||null; }
function setAirspaceVisibility(type, visible) {
  if(!(type in airspaceVisibility)) return;
  airspaceVisibility[type]=Boolean(visible);
  if(typeof currentGridMap !== 'undefined' && currentGridMap) drawMapGrids(currentGridMap);
}

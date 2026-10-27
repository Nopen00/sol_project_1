import type { KakaoMapSdk, MapInstance, PolygonInstance } from "./mapSdk";

const BASE = 1000; // 0.001 degrees in microdegrees
const SCALE = 1_000_000;
const MAX_VISIBLE = 3000;
const MERGES = [1, 3, 5, 9, 15];

function mergeForLevel(level: number): number {
  if (level <= 5) return 1;
  if (level <= 7) return 3;
  if (level <= 9) return 5;
  if (level <= 11) return 9;
  return 15;
}

export function createGridController(sdk: KakaoMapSdk, map: MapInstance) {
  const cells = new Map<string, PolygonInstance>();

  function clear() {
    cells.forEach(cell => cell.setMap(null));
    cells.clear();
  }

  function render() {
    const bounds = map.getBounds();
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const south = Math.max(33, sw.getLat());
    const north = Math.min(39, ne.getLat());
    const west = Math.max(124, sw.getLng());
    const east = Math.min(132, ne.getLng());
    if (south >= north || west >= east) { clear(); return; }

    let merge = mergeForLevel(map.getLevel());
    let step = BASE * merge;
    const count = (size: number) =>
      (Math.ceil(north * SCALE / size) - Math.floor(south * SCALE / size)) *
      (Math.ceil(east * SCALE / size) - Math.floor(west * SCALE / size));
    while (count(step) > MAX_VISIBLE) {
      merge += 2;
      step = BASE * merge;
    }

    const visible = new Set<string>();
    for (let row = Math.floor(south * SCALE / step); row < Math.ceil(north * SCALE / step); row++) {
      for (let col = Math.floor(west * SCALE / step); col < Math.ceil(east * SCALE / step); col++) {
        const key = `${step}:${row}:${col}`;
        visible.add(key);
        if (cells.has(key)) continue;
        const lat1 = row * step / SCALE;
        const lat2 = (row + 1) * step / SCALE;
        const lng1 = col * step / SCALE;
        const lng2 = (col + 1) * step / SCALE;
        cells.set(key, new sdk.Polygon({
          map,
          path: [[
            new sdk.LatLng(lat1, lng1), new sdk.LatLng(lat1, lng2),
            new sdk.LatLng(lat2, lng2), new sdk.LatLng(lat2, lng1),
          ]],
          strokeWeight: 1,
          strokeColor: "#4679a8",
          strokeOpacity: 0.65,
          fillColor: "#ffffff",
          fillOpacity: 0,
        }));
      }
    }
    for (const [key, cell] of cells) {
      if (!visible.has(key)) { cell.setMap(null); cells.delete(key); }
    }
  }
  return { render, clear };
}

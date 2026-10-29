
interface LatLng {
  getLat(): number;
  getLng(): number;
}

interface Polygon {
  setMap(map: unknown | null): void;
}

interface KakaoGridSdk {
  LatLng: new (lat: number, lng: number) => LatLng;
  Polygon: new (options: {
    map: unknown;
    path: LatLng[][];
    strokeWeight: number;
    strokeColor: string;
    strokeOpacity: number;
    fillColor: string;
    fillOpacity: number;
  }) => Polygon;
}

interface GridMap {
  getLevel(): number;
  getBounds(): {
    getSouthWest(): LatLng;
    getNorthEast(): LatLng;
  };
}

const BASE = 1000;
const SCALE = 1_000_000;
const MAX_VISIBLE = 3000;

function mergeForLevel(level: number): number {
  if (level <= 5) return 1;
  if (level <= 7) return 3;
  if (level <= 9) return 5;
  if (level <= 11) return 9;
  return 15;
}

export function createGridController(
  sdk: KakaoGridSdk,
  map: GridMap,
) {
  const cells = new Map<string, Polygon>();

  function clear() {
    cells.forEach((cell) => cell.setMap(null));
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

    if (south >= north || west >= east) {
      clear();
      return;
    }

    let merge = mergeForLevel(map.getLevel());
    let step = BASE * merge;

    const count = (size: number) =>
      (Math.ceil(north * SCALE / size) -
        Math.floor(south * SCALE / size)) *
      (Math.ceil(east * SCALE / size) -
        Math.floor(west * SCALE / size));

    while (count(step) > MAX_VISIBLE) {
      merge += 2;
      step = BASE * merge;
    }

    const visible = new Set<string>();

    for (
      let row = Math.floor(south * SCALE / step);
      row < Math.ceil(north * SCALE / step);
      row++
    ) {
      for (
        let col = Math.floor(west * SCALE / step);
        col < Math.ceil(east * SCALE / step);
        col++
      ) {
        const key = `${step}:${row}:${col}`;
        visible.add(key);

        if (cells.has(key)) continue;

        const lat1 = row * step / SCALE;
        const lat2 = (row + 1) * step / SCALE;
        const lng1 = col * step / SCALE;
        const lng2 = (col + 1) * step / SCALE;

        const polygon = new sdk.Polygon({
          map,
          path: [[
            new sdk.LatLng(lat1, lng1),
            new sdk.LatLng(lat1, lng2),
            new sdk.LatLng(lat2, lng2),
            new sdk.LatLng(lat2, lng1),
          ]],
          strokeWeight: 1,
          strokeColor: "#4679a8",
          strokeOpacity: 0.65,
          fillColor: "#ffffff",
          fillOpacity: 0,
        });

        cells.set(key, polygon);
      }
    }

    for (const [key, cell] of cells) {
      if (!visible.has(key)) {
        cell.setMap(null);
        cells.delete(key);
      }
    }
  }

  return { render, clear };
}

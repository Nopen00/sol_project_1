
import type { DroneModel } from "../types/drone";

export async function getDroneModels(): Promise<DroneModel[]> {
  const response = await fetch("http://127.0.0.1:8000/drones");

  if (!response.ok) {
    throw new Error(`드론 목록 조회 실패: ${response.status}`);
  }

  const drones: DroneModel[] = await response.json();

  return drones;
}

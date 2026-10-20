import type { DroneModel } from "../types/drone";

const SAMPLE_DRONES: DroneModel[] = [
  { id: "sample-mini", name: "예시 소형 드론" },
  { id: "sample-air", name: "예시 중형 드론" },
  { id: "sample-pro", name: "예시 대형 드론" },
];

export async function getDroneModels(): Promise<DroneModel[]> {
  return SAMPLE_DRONES;
}

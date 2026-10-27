// API 기본 주소는 Vite 환경변수로 설정합니다.
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api"
).replace(/\/$/, "");

export async function getJson<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const query = params ? `?${new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)]))}` : "";
  const response = await fetch(`${API_BASE_URL}${path}${query}`);
  if (!response.ok) {
    throw new Error(`API 요청 실패 (${response.status}): ${path}`);
  }
  return response.json() as Promise<T>;
}

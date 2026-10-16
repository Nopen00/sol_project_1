export async function getWeather(lat: number, lon: number) {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
  })

  const response = await fetch(`/api/weather?${params}`)

  if (!response.ok) {
    throw new Error(`기상정보 조회 실패: ${response.status}`)
  }

  return response.json()
}
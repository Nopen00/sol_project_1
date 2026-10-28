
import type { NewsVideosResponse } from "../types/news";

export async function getNewsVideos(): Promise<NewsVideosResponse> {
  const response = await fetch("/api/news/videos");

  if (!response.ok) {
    throw new Error(`영상 목록 조회 실패: ${response.status}`);
  }

  const videos: NewsVideosResponse = await response.json();

  return videos;
}

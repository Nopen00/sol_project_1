import requests
from app.core.config import settings
from datetime import datetime, timedelta, timezone,date
import json
from pathlib import Path
from app.models.youtube_video import YoutubeVideo
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import delete
from app.models.database import SessionLocal
import html



URL = "https://www.googleapis.com/youtube/v3/search"
SAMPLE_PATH = Path(__file__).resolve().parents[3] / "data" / "sample" / "yt_sample.json"
MAX_VIDEO = 6


# 유튜브에 params 조건으로 검색하라!
def search_by_keyword():
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 조건
    params = {
        "part": "id,snippet",
        "q": "드론 -쇼",
        "maxResults": MAX_VIDEO,
        "type": "video",
        "order": "date",
        "regionCode": "KR",
        "relevanceLanguage": "ko",
        "publishedAfter": week_ago,
        "key": settings.yt_api,
    }

    res = requests.get(URL, params, timeout=10)

    res.raise_for_status()
    results = res.json()

    for item in results["items"]:
        print("[%s] Title: %s" % (item["id"].get("videoId"), item["snippet"]["title"]))
        print(f"{item}")

    return results

# 영상 객체 쪼개기 => results에는 n개의 영상이 있다 그것을 1개씩 분리해서 data로 반환
def extract_videos(results):

    data = []
    for item in results["items"]:
        data.append({
            "video_id" : item["id"]["videoId"],
            "thumbnail_url" :item["snippet"]["thumbnails"]["medium"]["url"],
            "title" : html.unescape(item["snippet"]["title"]),
            "channel_title" : html.unescape(item["snippet"]["channelTitle"]),
            "published_at" : item["snippet"]["publishedAt"],
            "saved_date" : date.today().isoformat()
        })

    return data

# api에서 받아온 정보를 db로 넣어줘라
def save_youtube_db(db : Session, results):

    videos = []
    data = extract_videos(results)

    for item in data:
        video = YoutubeVideo(
            video_id=item['video_id'],
            thumbnail_url = item['thumbnail_url'],
            title = item['title'],
            channel_title = item['channel_title'],
            # fromisoformat : "2026-10-23T05:00:00Z" 유튜브와 소통하는 시간대 규칙을 UTC기본 정보로 전환
            # replace(tzinfo=None) : 날짜와 시간표만 표시 UTC 꼬리표 제거
            published_at = datetime.fromisoformat(item['published_at']).replace(tzinfo=None),
        )
        videos.append(video)

    # 기존 삭제
    db.execute(delete(YoutubeVideo)) 
    db.add_all(videos)
    db.commit()

    return data


def save_youtube_json(results):

    data = extract_videos(results)

    with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        data_json = json.load(f)
    print(f"json 저장 확인 : {data_json}")


# 오늘 유튜브 새로 받기
def save_new_data():
    results = search_by_keyword()
    with SessionLocal() as db:

        try:
            return save_youtube_db(db ,results)
        except OperationalError:
            save_youtube_json(results)
            return None
    



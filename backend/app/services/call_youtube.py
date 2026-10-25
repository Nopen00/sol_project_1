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


def save_youtube_db(db : Session, results):

    videos = []
    data = extract_videos(results)

    for item in data:
        video = YoutubeVideo(
            video_id=item['video_id'],
            thumbnail_url = item['thumbnail_url'],
            title = item['title'],
            channel_title = item['channel_title'],
            published_at = datetime.fromisoformat(item['published_at']).replace(tzinfo=None),
        )
        videos.append(video)
    
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



if __name__ == "__main__":
    results = search_by_keyword()
    with SessionLocal() as db:

        try:
            save_youtube_db(db ,results)
        except OperationalError:
            save_youtube_json(results)



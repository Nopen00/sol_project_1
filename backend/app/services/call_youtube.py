import requests
from app.core.config import settings
from datetime import datetime, timedelta, timezone,date
import json
from pathlib import Path


URL = "https://www.googleapis.com/youtube/v3/search"
SAMPLE_PATH = Path(__file__).resolve().parents[3] / "data" / "sample" / "yt_sample.json"


def search_by_keyword():
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "part": "id,snippet",
        "q": "드론 -쇼",
        "maxResults": 6,
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


def save_youtube_db():
    pass


def save_youtube_json(results):
    data = []
    # dum = []

    for item in results["items"]:
        
        data.append({
            "video_id" : item["id"]["videoId"],
            "thumbnail_url" :item["snippet"]["thumbnails"]["medium"]["url"],
            "title" : item["snippet"]["title"],
            "channel_title" : item["snippet"]["channelTitle"],
            "published_at" : item["snippet"]["publishedAt"],
            "saved_date" : date.today().isoformat()
        })


    # data.append(dum)
    
    with open(SAMPLE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        data_json = json.load(f)
    print(f"json 저장 확인 : {data_json}")


if __name__ == "__main__":
    results = search_by_keyword()

    # db 붙으면 db 오류나면 반환하는걸로 수정해서 전환
    # if (save_youtube_db(results) == False|None):
    #     save_youtube_json(results)

    # 위에 만들어지기 전까지 임시용
    save_youtube_json(results)

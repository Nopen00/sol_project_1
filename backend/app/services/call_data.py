from sqlalchemy.orm import Session
from sqlalchemy import select 
from app.models.youtube_video import YoutubeVideo
from datetime import date
from app.services.call_youtube import save_new_data
from app.models.database import SessionLocal
from sqlalchemy.exc import OperationalError
from app.services.call_youtube import SAMPLE_PATH
import json


# db에 저장된 데이터가 오늘거면 반환, 아니면 새로 받아와
def get_videos(db :Session):
    try:
        videos = get_today_videos_db(db)
        if not videos:
            dum = save_new_data()
            if dum is None:
                videos = get_videos_json()
            else:
                videos = get_today_videos_db(db)
    except(OperationalError):
        videos = get_videos_json()

    return videos

     

# db의 저장된 데이터가 오늘의 데이터인지 확인
def get_today_videos_db(db: Session):
    stmt = select(YoutubeVideo).where(YoutubeVideo.saved_date == date.today())
    return db.execute(stmt).scalars().all()



def get_videos_json():
    with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
        data_json = json.load(f)
    # print(f"json 저장 확인 : {data_json}")

    return data_json



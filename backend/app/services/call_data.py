from sqlalchemy.orm import Session
from sqlalchemy import select 
from app.models.youtube_video import YoutubeVideo
from datetime import date
from app.services.call_youtube import save_new_data
from app.models.database import SessionLocal


# db에 저장된 데이터가 오늘거면 반환, 아니면 새로 받아와
def get_videos_db(db :Session):
    videos = get_today_videos(db)
    if not videos:
        save_new_data()
    videos = get_today_videos(db)
    return videos

    

# db의 저장된 데이터가 오늘의 데이터인지 확인
def get_today_videos(db: Session):
    stmt = select(YoutubeVideo).where(YoutubeVideo.saved_date == date.today())
    return db.execute(stmt).scalars().all()


def get_videos_json():
    pass


def print_videos():
    pass
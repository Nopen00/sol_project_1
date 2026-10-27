from fastapi import APIRouter, Depends
from app.schemas.youtube import YoutubeResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.call_data import get_videos


youtube_router = APIRouter(prefix="/api/news", tags=["news"])


@youtube_router.get("/videos", response_model=YoutubeResponse)
def get_list_videos(db:Session = Depends(get_db)):
    videos = get_videos(db=db)
    return {'items': videos}
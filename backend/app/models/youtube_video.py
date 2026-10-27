from sqlalchemy import (
    DateTime,
    Date,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.models.database import Base
from datetime import datetime, date


# video_id (PK), thumbnail_url, title, channel_title, published_at, saved_date
class YoutubeVideo(Base):

    __tablename__ = "youtube_videos"
    __table_args__ = {'schema':'DRONE_APP'}

    video_id: Mapped[str] = mapped_column(String(20), nullable=False, primary_key=True)
    thumbnail_url: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    channel_title: Mapped[str] = mapped_column(String(100), nullable=False)

    published_at: Mapped[datetime] = mapped_column(DateTime)
    saved_date: Mapped[date] = mapped_column(Date, default=date.today)

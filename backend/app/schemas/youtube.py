from pydantic import BaseModel
from datetime import datetime
from pydantic import field_validator
from datetime import timezone, timedelta

KST = timezone(timedelta(hours=9))

# event 하나 조회 => 테이블 구조와 동일
class YoutubeItem(BaseModel):

    video_id: str  # 자동 생성되는 고유 식별자
    thumbnail_url:str
    title:str
    channel_title:str
    published_at:datetime

    model_config = {'from_attributes':True}

    # 아래 함수를 통해 published_at에 들어가는 값을 통일
    # DB는 날짜 + 시간, JSON은 날짜 + 시간 + UTC표시까지 였던걸
    # 날짜 + 시간 +  kst로 변환
    @field_validator("published_at")
    @classmethod
    def to_kst(cls, value: datetime) -> datetime:
        if value.tzinfo is None:                    # DB에서 온 값: 시간대 없음 → UTC로 간주
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(KST) 

        


class YoutubeResponse(BaseModel):
    items:list[YoutubeItem]
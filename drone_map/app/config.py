
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

KAKAO_API_KEY = os.getenv("KAKAO_MAP_API_KEY")
KMA_SERVICE_KEY = os.getenv("KMA_SERVICE_KEY")

KST = ZoneInfo("Asia/Seoul")

KMA_URL = (
    "https://apis.data.go.kr/1360000/"
    "VilageFcstInfoService_2.0"
)

CACHE_SECONDS = 600
MAX_GRID_COUNT = 40
MAX_CONCURRENT_REQUESTS = 4

# 키 내용은 출력하지 않고 로딩 여부만 확인
print(f".env 파일 존재: {ENV_PATH.is_file()}")
print(f"카카오 API 키 로딩: {bool(KAKAO_API_KEY)}")
print(f"기상청 API 키 로딩: {bool(KMA_SERVICE_KEY)}")

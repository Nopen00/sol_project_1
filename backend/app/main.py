
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.youtube import youtube_router
from app.routers.drones import router as drones_router
from app.routers.airspace import router as airspace_router
from app.routers.flight_analysis import router as flight_analysis_router
from app.routers.weather_national import router as weather_national_router
from app.routers.weather import router as weather_router

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # 어떤 출처의 요청을 허용할 것인가?
    # allow_credentials=True, # 쿠키나 인증정보를 포함한 요청을 허용할 것인가?
    allow_methods=["*"],  # 어떤 메소드를 허용할 것인가? (post, get, put, patch, delete)
    allow_headers=["*"]   # 요청에서 사용할 수 있는 헤더정보
)

app.include_router(youtube_router)

# 드론 데이터 조회
app.include_router(drones_router)

# 비행금지구역 및 비행제한구역 조회
app.include_router(airspace_router)

# 드론 비행 분석
app.include_router(flight_analysis_router)

# 전국 날씨 조회
app.include_router(weather_national_router)

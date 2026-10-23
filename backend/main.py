from app.core.config import get_settings
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

from app.routers.airspace import router as airspace_router
from app.routers.drones import router as drones_router
from app.routers.flight_analysis import router as flight_analysis_router

from app.routers.regions import router as regions_router

from app.routers.weather import router as weather_router


app = FastAPI(title="드론 공역 API 테스트")
logger = logging.getLogger(__name__)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    # SQL 문장, DB 접속 정보, 드라이버 메시지는 응답에 포함하지 않습니다.
    logger.error("Database operation failed at %s", request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": "데이터베이스를 일시적으로 사용할 수 없습니다."},
    )

# 카카오맵 테스트 페이지의 API 요청 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# 공역 조회 API 연결
app.include_router(airspace_router)
# 드론 정보 API 연결
app.include_router(drones_router)
app.include_router(flight_analysis_router)

app.include_router(regions_router)
app.include_router(weather_router)

@app.get("/")
def home():
    return {"message": "드론 공역 API 서버 실행 성공"}

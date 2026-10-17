from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.airspace import router as airspace_router

app = FastAPI(title="드론 공역 API 테스트")

# 카카오맵 테스트 페이지의 API 요청 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# 공역 조회 API 연결
app.include_router(airspace_router)


@app.get("/")
def home():
    return {"message": "드론 공역 API 서버 실행 성공"}

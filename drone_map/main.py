
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router

app = FastAPI(title="드론 기상 위험 지도")

app.include_router(router)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

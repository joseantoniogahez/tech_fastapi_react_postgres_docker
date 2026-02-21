from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.const.settings import ApiSettings


def configure_cors(app: FastAPI, settings: ApiSettings) -> None:
    origins = [origin.strip() for origin in settings.API_CORS_ORIGINS.split(",") if origin.strip()]
    if not origins:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

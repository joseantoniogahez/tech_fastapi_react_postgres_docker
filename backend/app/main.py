from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.const.settings import ApiSettings
from app.routers import author, book


def _attach_app_cors(app: FastAPI) -> None:
    origins = ApiSettings().API_CORS_ORIGINS.split(",")
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


def _attach_app_routers(app: FastAPI) -> None:
    app.include_router(book.router)
    app.include_router(author.router)


def create_app() -> FastAPI:
    root_path = ApiSettings().API_PATH
    app = FastAPI(root_path=root_path)
    _attach_app_cors(app)
    _attach_app_routers(app)
    return app


app = create_app()

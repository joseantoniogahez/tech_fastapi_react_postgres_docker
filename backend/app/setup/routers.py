from fastapi import FastAPI

from app.routers import auth, author, book, health


def configure_routers(app: FastAPI) -> None:
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(book.router)
    app.include_router(author.router)

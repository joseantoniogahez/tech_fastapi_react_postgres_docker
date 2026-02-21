from fastapi import FastAPI


def configure_exception_handlers(app: FastAPI) -> None:
    # Centralized extension point for custom exception handlers.
    pass

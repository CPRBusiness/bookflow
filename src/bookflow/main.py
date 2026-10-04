from fastapi import FastAPI

from bookflow.app.api.health import router as health_router
from bookflow.app.api.auth import router as auth_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="BookFlow API",
        description="Multi-tenant appointment management platform",
        version="0.1.0",
    )

    application.include_router(health_router)
    application.include_router(auth_router)

    return application


app = create_app()
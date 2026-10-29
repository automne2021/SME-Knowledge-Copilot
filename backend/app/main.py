import uuid

from fastapi import FastAPI, Request

from app.api.router import api_router
from app.core.errors import register_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="SME AI Operations Copilot API", version="0.1.0")

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

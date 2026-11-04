import threading
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        yield
        runtime = getattr(app.state, "search_runtime", None)
        if runtime is not None:
            runtime.close()
            app.state.search_runtime = None

    app = FastAPI(title="SME Knowledge Copilot API", version="0.3.0", lifespan=lifespan)
    app.state.search_init_lock = threading.Lock()
    app.state.llm_capacity = threading.BoundedSemaphore(get_settings().llm_max_concurrency)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        return response

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

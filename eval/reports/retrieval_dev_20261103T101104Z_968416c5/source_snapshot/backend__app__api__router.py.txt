from fastapi import APIRouter

from app.api import health, identity, resources, search, uploads

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router)
api_router.include_router(resources.router)
api_router.include_router(uploads.router)
api_router.include_router(search.router)

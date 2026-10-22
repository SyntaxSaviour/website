from fastapi import APIRouter
from app.api.v1.endpoints import services, content, seo, health
from app.api.v1.endpoints.admin import content as admin_content

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(seo.router, tags=["SEO"])
api_router.include_router(admin_content.router, prefix="/admin/content", tags=["Admin Content"])
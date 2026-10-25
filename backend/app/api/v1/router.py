from fastapi import APIRouter
<<<<<<< HEAD
from app.api.v1.endpoints import services, content, seo, health, enquiries, contact
from app.api.v1.endpoints.admin import content as admin_content
from app.api.v1.endpoints.admin import enquiries as admin_enquiries
from app.api.v1.endpoints.admin import auth as admin_auth

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(seo.router, tags=["SEO"])

# Public form submissions
api_router.include_router(enquiries.router, prefix="/enquiries", tags=["Enquiries"])
api_router.include_router(contact.router, prefix="/contact", tags=["Contact"])

# Admin Authentication (Fixes the 404 errors)
api_router.include_router(admin_auth.router, prefix="/admin/auth", tags=["Admin Auth"])

# Admin Management
=======

from app.api.v1.endpoints import (
    services,
    content,
    seo,
    health,
    enquiries,
    contact,
)
from app.api.v1.endpoints.admin import auth as admin_auth
from app.api.v1.endpoints.admin import content as admin_content
from app.api.v1.endpoints.admin import enquiries as admin_enquiries

api_router = APIRouter()

# Public Services & Dynamic Content
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(seo.router, tags=["SEO"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Enquiries & Contact
api_router.include_router(enquiries.router, prefix="/enquiries", tags=["Enquiries"])
api_router.include_router(contact.router, prefix="/contact", tags=["Contact"])

# Admin Routes
api_router.include_router(admin_auth.router, prefix="/admin/auth", tags=["Admin Auth"])
>>>>>>> dfcbd30b9be2441de778c8562dc6a0327756a581
api_router.include_router(admin_content.router, prefix="/admin/content", tags=["Admin Content"])
api_router.include_router(admin_enquiries.router, prefix="/admin/enquiries", tags=["Admin Enquiries"])
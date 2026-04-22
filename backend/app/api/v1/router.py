"""
Central API router — registers ALL module routers.
Every module added here is automatically exposed under /api/v1/
"""
from fastapi import APIRouter

# Foundation
from app.core.auth.router import router as auth_router
from app.core.documents.router import router as documents_router
from app.core.constitutional.router import router as constitutional_router
from app.api.v1.users import router as users_router

# QMS
from app.modules.qms.router import router as qms_router

# MES
from app.modules.mes.router import router as mes_router

# Equipment
from app.modules.equipment.router import router as equipment_router

# Training
from app.modules.training.router import router as training_router

# Environmental Monitoring
from app.modules.env_monitoring.router import router as env_monitoring_router

# LIMS
from app.modules.lims.router import router as lims_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(documents_router)
api_router.include_router(constitutional_router)
api_router.include_router(qms_router)
api_router.include_router(mes_router)
api_router.include_router(equipment_router)
api_router.include_router(training_router)
api_router.include_router(env_monitoring_router)
api_router.include_router(lims_router)

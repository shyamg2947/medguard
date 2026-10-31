"""
MedGuard FastAPI Main Application.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes_admin import router as admin_router
from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_caregivers import router as caregivers_router
from backend.app.api.routes_monitoring import router as monitoring_router
from backend.app.api.routes_patients import router as patients_router
from backend.app.api.routes_reports import router as reports_router
from backend.app.api.routes_review import router as review_router
from backend.app.channels.simulator import router as simulator_router
from backend.app.channels.whatsapp import router as whatsapp_router
from backend.app.config import get_settings
from backend.app.models.db import SessionLocal, User, generate_uuid, init_db, utc_now


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables created and demo accounts provisioned
    init_db()
    db = SessionLocal()
    try:
        roles = [
            ("DEMO-SENIOR", "senior"),
            ("DEMO-CAREGIVER", "caregiver"),
            ("DEMO-CLINICIAN", "clinician"),
            ("DEMO-ADMIN", "admin"),
        ]
        for token, role in roles:
            existing = db.query(User).filter(User.display_token == token).first()
            if not existing:
                u = User(
                    id=f"user-{role}",
                    role=role,
                    display_token=token,
                    preferred_language="en",
                    active=True,
                    created_at=utc_now(),
                )
                db.add(u)
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title="MedGuard Decision-Support API",
    description="Voice-first, multilingual medication-safety assistant for seniors",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(reports_router)
app.include_router(review_router)
app.include_router(caregivers_router)
app.include_router(monitoring_router)
app.include_router(admin_router)
app.include_router(whatsapp_router)
app.include_router(simulator_router)


@app.get("/healthz", tags=["Health"])
def healthz():
    return {"status": "ok", "service": "medguard-api", "mode": get_settings().MODE}


@app.get("/readyz", tags=["Health"])
def readyz():
    return {"ready": True, "free_tier_mode": get_settings().FREE_TIER_MODE}


# Serve built frontend SPA if frontend/dist exists
frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

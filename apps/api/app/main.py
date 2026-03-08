from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.backend_ui import router as backend_ui_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.scheduler import start_scheduler, stop_scheduler
from app.services.commissions import close_weekly_commissions

@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.auto_create_tables:
        init_db()
    if settings.enable_commission_scheduler:
        start_scheduler()
    if settings.commission_scheduler_run_on_startup:
        db = SessionLocal()
        try:
            close_weekly_commissions(db, previous_week=True)
        finally:
            db.close()
    yield
    if settings.enable_commission_scheduler:
        stop_scheduler()


app = FastAPI(title=settings.project_name, lifespan=lifespan)

cors_origins = [item.strip() for item in settings.cors_allow_origins.split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(backend_ui_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Mande24 Independent API running"}

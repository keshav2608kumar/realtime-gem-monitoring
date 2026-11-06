"""
GeM BidWatch — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.workers.scheduler import start_scheduler, stop_scheduler
from app.routers import profiles, bids, alerts, health, devices

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── LIFESPAN ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 GeM BidWatch starting up...")
    init_db()
    logger.info("✅ Database initialized")
    start_scheduler()
    yield
    logger.info("🛑 GeM BidWatch shutting down...")
    stop_scheduler()


# ─── APP ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GeM BidWatch API",
    description="24/7 GeM bid monitoring with Android alarm notifications",
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

# ─── ROUTERS ──────────────────────────────────────────────────────────────────
app.include_router(profiles.router)
app.include_router(bids.router)
app.include_router(alerts.router)
app.include_router(health.router)
app.include_router(devices.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": "GeM BidWatch",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }

"""
GeM BidWatch — APScheduler setup
Runs the monitor worker on a fixed interval.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.settings import settings
from app.workers.monitor_worker import poll_all_active_profiles

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()


def start_scheduler():
    if not settings.MONITOR_ENABLED:
        logger.info("Monitor is DISABLED via settings. Skipping scheduler start.")
        return

    _scheduler.add_job(
        func=poll_all_active_profiles,
        trigger=IntervalTrigger(seconds=settings.GEM_POLL_INTERVAL_SECONDS),
        id="gem_monitor",
        name="GeM Bid Monitor",
        replace_existing=True,
        max_instances=1,  # Never run two polls simultaneously
    )
    _scheduler.start()
    logger.info(f"Scheduler started. Polling every {settings.GEM_POLL_INTERVAL_SECONDS}s.")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


def get_scheduler_status() -> dict:
    jobs = _scheduler.get_jobs()
    return {
        "running": _scheduler.running,
        "jobs": [
            {
                "id": j.id,
                "name": j.name,
                "next_run": str(j.next_run_time),
            }
            for j in jobs
        ],
    }

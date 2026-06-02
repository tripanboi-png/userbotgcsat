"""
APScheduler wrapper for autogcast tasks.
Uses AsyncIOScheduler with asyncio event loop.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils.logger import logger

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone="UTC")

# Registry: task_id -> job_id (APScheduler job ID)
_job_registry: dict[str, str] = {}


def start_scheduler():
    """Start the APScheduler if not already running."""
    if not scheduler.running:
        scheduler.start()
        logger.info("[Scheduler] APScheduler started.")


def stop_scheduler():
    """Shutdown the APScheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] APScheduler stopped.")


def add_job(task_id: str, func, interval_minutes: int, **kwargs) -> str:
    """
    Add a recurring job to the scheduler.
    Returns the APScheduler job ID.
    """
    job_id = f"job_{task_id}"

    # Remove existing job if present
    remove_job(task_id)

    trigger = IntervalTrigger(minutes=interval_minutes)
    scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        kwargs=kwargs,
        misfire_grace_time=60,
        coalesce=True,
    )
    _job_registry[task_id] = job_id
    logger.info(f"[Scheduler] Job '{job_id}' added, interval={interval_minutes}m")
    return job_id


def remove_job(task_id: str) -> bool:
    """Remove a scheduled job by task_id. Returns True if removed."""
    job_id = f"job_{task_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        _job_registry.pop(task_id, None)
        logger.info(f"[Scheduler] Job '{job_id}' removed.")
        return True
    return False


def remove_all_jobs():
    """Remove all scheduled jobs."""
    scheduler.remove_all_jobs()
    _job_registry.clear()
    logger.info("[Scheduler] All jobs removed.")


def get_job_info(task_id: str) -> dict | None:
    """Return next run time and other info for a job."""
    job_id = f"job_{task_id}"
    job = scheduler.get_job(job_id)
    if not job:
        return None
    return {
        "job_id": job_id,
        "next_run": job.next_run_time,
        "trigger": str(job.trigger),
    }


def list_jobs() -> list[dict]:
    """List all active scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "job_id": job.id,
            "next_run": job.next_run_time,
            "trigger": str(job.trigger),
        })
    return jobs

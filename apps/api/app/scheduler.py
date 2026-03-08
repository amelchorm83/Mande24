from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.commissions import close_weekly_commissions

scheduler = BackgroundScheduler(timezone="UTC")


def _run_weekly_close_job() -> None:
    db = SessionLocal()
    try:
        # Monday job closes previous week snapshots.
        close_weekly_commissions(db, previous_week=True)
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        _run_weekly_close_job,
        trigger=CronTrigger(day_of_week="mon", hour=settings.commission_close_hour_utc, minute=settings.commission_close_minute_utc),
        id="weekly_commission_close",
        replace_existing=True,
    )
    scheduler.start()



def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

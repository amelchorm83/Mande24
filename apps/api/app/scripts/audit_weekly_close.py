from datetime import date, datetime, timezone

import httpx

from app.core.config import settings
from app.db.init_db import init_db
from app.db.models import RiderCommission, StationCommission
from app.db.session import SessionLocal
from app.services.commissions import close_weekly_commissions


def check_api_health() -> tuple[bool, str]:
    health_url = "http://localhost:8000/api/v1/health"
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(health_url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return True, f"health_ok url={health_url}"
            return False, f"health_unexpected status_code={response.status_code}"
    except Exception as exc:
        return False, f"health_unreachable reason={exc}"


def main() -> None:
    if settings.auto_create_tables:
        init_db()

    health_ok, health_msg = check_api_health()
    print(health_msg)

    db = SessionLocal()
    try:
        result = close_weekly_commissions(db, previous_week=True)
        week_start = result["week_start"]

        week_start_date = date.fromisoformat(week_start)
        rider_count = db.query(RiderCommission).filter(RiderCommission.week_start == week_start_date).count()
        station_count = db.query(StationCommission).filter(StationCommission.week_start == week_start_date).count()

        print(
            "weekly_close_audit",
            f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
            f"week_start={week_start}",
            f"rider_snapshots={rider_count}",
            f"station_snapshots={station_count}",
            f"api_health={health_ok}",
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.commissions import close_weekly_commissions


def main() -> None:
    if settings.auto_create_tables:
        init_db()

    db = SessionLocal()
    try:
        result = close_weekly_commissions(db, previous_week=True)
        print(
            "weekly_commission_close",
            f"week_start={result['week_start']}",
            f"rider_snapshots={result['rider_snapshots']}",
            f"station_snapshots={result['station_snapshots']}",
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

from app.db.base import Base
from app.db.geo_seed import seed_geo_catalogs
from app.db.session import engine
from app.db.session import SessionLocal


def init_db() -> None:
    # Local bootstrap convenience; staging/prod should use Alembic migrations.
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_geo_catalogs(db)
    finally:
        db.close()

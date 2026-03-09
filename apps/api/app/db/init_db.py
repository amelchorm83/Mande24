from app.db.base import Base
from app.db.geo_seed import seed_geo_catalogs
from app.db.sepomex_sync import sync_sepomex_catalog
from app.db.session import engine
from app.db.session import SessionLocal
from sqlalchemy import inspect, text


def _ensure_runtime_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "client_profiles" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("client_profiles")}
    if "colony_id" in columns:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE client_profiles ADD COLUMN colony_id VARCHAR(64)"))


def init_db() -> None:
    # Local bootstrap convenience; staging/prod should use Alembic migrations.
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_schema()
    db = SessionLocal()
    try:
        try:
            sync_sepomex_catalog(db)
        except Exception:
            # Fallback to built-in catalog to keep bootstrap resilient without network.
            seed_geo_catalogs(db)
    finally:
        db.close()

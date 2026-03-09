from app.db.base import Base
from app.db.geo_seed import seed_geo_catalogs
from app.db.sepomex_sync import sync_sepomex_catalog
from app.db.session import engine
from app.db.session import SessionLocal
from sqlalchemy import inspect, text


def _ensure_runtime_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "user_role_audits" in tables:
        audit_columns = {col["name"] for col in inspector.get_columns("user_role_audits")}
        with engine.begin() as conn:
            if "changed_by_user_id" not in audit_columns:
                conn.execute(text("ALTER TABLE user_role_audits ADD COLUMN changed_by_user_id VARCHAR(32)"))
            if "changed_by_email" not in audit_columns:
                conn.execute(text("ALTER TABLE user_role_audits ADD COLUMN changed_by_email VARCHAR(190)"))

    if "client_profiles" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("client_profiles")}
    with engine.begin() as conn:
        if "colony_id" not in columns:
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN colony_id VARCHAR(64)"))
        if "landline_phone" not in columns:
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN landline_phone VARCHAR(40) DEFAULT ''"))
        if "whatsapp_phone" not in columns:
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN whatsapp_phone VARCHAR(40) DEFAULT ''"))

    if "riders" in tables:
        rider_columns = {col["name"] for col in inspector.get_columns("riders")}
        with engine.begin() as conn:
            if "landline_phone" not in rider_columns:
                conn.execute(text("ALTER TABLE riders ADD COLUMN landline_phone VARCHAR(40) DEFAULT ''"))
            if "whatsapp_phone" not in rider_columns:
                conn.execute(text("ALTER TABLE riders ADD COLUMN whatsapp_phone VARCHAR(40) DEFAULT ''"))

    if "stations" in tables:
        station_columns = {col["name"] for col in inspector.get_columns("stations")}
        with engine.begin() as conn:
            if "landline_phone" not in station_columns:
                conn.execute(text("ALTER TABLE stations ADD COLUMN landline_phone VARCHAR(40) DEFAULT ''"))
            if "whatsapp_phone" not in station_columns:
                conn.execute(text("ALTER TABLE stations ADD COLUMN whatsapp_phone VARCHAR(40) DEFAULT ''"))

    if "contact_leads" not in tables:
        return

    lead_columns = {col["name"] for col in inspector.get_columns("contact_leads")}
    with engine.begin() as conn:
        if "status" not in lead_columns:
            conn.execute(text("ALTER TABLE contact_leads ADD COLUMN status VARCHAR(20) DEFAULT 'new'"))
            conn.execute(text("UPDATE contact_leads SET status = 'new' WHERE status IS NULL OR status = ''"))
        if "updated_at" not in lead_columns:
            conn.execute(text("ALTER TABLE contact_leads ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE"))
            conn.execute(text("UPDATE contact_leads SET updated_at = created_at WHERE updated_at IS NULL"))


def init_db() -> None:
    # Local bootstrap convenience; staging/prod should use Alembic migrations.
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_schema()
    db = SessionLocal()
    try:
        try:
            sync_sepomex_catalog(db)
        except Exception:
            db.rollback()
            # Fallback to built-in catalog to keep bootstrap resilient without network.
            seed_geo_catalogs(db)
    finally:
        db.close()

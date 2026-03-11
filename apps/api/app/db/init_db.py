from app.db.base import Base
from app.db.geo_seed import seed_geo_catalogs
from app.db.models import User, UserRoleLink
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
        guide_columns = {col["name"] for col in inspector.get_columns("guides")} if "guides" in tables else set()
        with engine.begin() as conn:
            if "guides" in tables and "destination_station_id" not in guide_columns:
                conn.execute(text("ALTER TABLE guides ADD COLUMN destination_station_id VARCHAR(32)"))
        return

    if "guides" in tables:
        guide_columns = {col["name"] for col in inspector.get_columns("guides")}
        with engine.begin() as conn:
            if "destination_station_id" not in guide_columns:
                conn.execute(text("ALTER TABLE guides ADD COLUMN destination_station_id VARCHAR(32)"))

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

    if "pricing_rules" in tables:
        pricing_columns = {col["name"] for col in inspector.get_columns("pricing_rules")}
        with engine.begin() as conn:
            if "pickup_fee" not in pricing_columns:
                conn.execute(text("ALTER TABLE pricing_rules ADD COLUMN pickup_fee FLOAT DEFAULT 0"))
            if "delivery_fee" not in pricing_columns:
                conn.execute(text("ALTER TABLE pricing_rules ADD COLUMN delivery_fee FLOAT DEFAULT 0"))
            if "transfer_fee" not in pricing_columns:
                conn.execute(text("ALTER TABLE pricing_rules ADD COLUMN transfer_fee FLOAT DEFAULT 0"))
            if "station_fee" not in pricing_columns:
                conn.execute(text("ALTER TABLE pricing_rules ADD COLUMN station_fee FLOAT DEFAULT 0"))

    if "route_legs" in tables:
        route_columns = {col["name"] for col in inspector.get_columns("route_legs")}
        with engine.begin() as conn:
            if "rider_fee_amount" not in route_columns:
                conn.execute(text("ALTER TABLE route_legs ADD COLUMN rider_fee_amount FLOAT DEFAULT 0"))
            if "station_fee_amount" not in route_columns:
                conn.execute(text("ALTER TABLE route_legs ADD COLUMN station_fee_amount FLOAT DEFAULT 0"))
            if "currency" not in route_columns:
                conn.execute(text("ALTER TABLE route_legs ADD COLUMN currency VARCHAR(10) DEFAULT 'MXN'"))

    if "guide_parties" in tables:
        party_columns = {col["name"] for col in inspector.get_columns("guide_parties")}
        with engine.begin() as conn:
            if "origin_landline_phone" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_landline_phone VARCHAR(40) DEFAULT ''"))
            if "origin_whatsapp_phone" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_whatsapp_phone VARCHAR(40) DEFAULT ''"))
            if "origin_email" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_email VARCHAR(190) DEFAULT ''"))
            if "origin_state_code" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_state_code VARCHAR(10) DEFAULT ''"))
            if "origin_municipality_code" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_municipality_code VARCHAR(20) DEFAULT ''"))
            if "origin_postal_code" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_postal_code VARCHAR(10) DEFAULT ''"))
            if "origin_colony_id" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_colony_id VARCHAR(64) DEFAULT ''"))
            if "origin_address_line" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN origin_address_line VARCHAR(255) DEFAULT ''"))
            if "destination_landline_phone" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_landline_phone VARCHAR(40) DEFAULT ''"))
            if "destination_whatsapp_phone" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_whatsapp_phone VARCHAR(40) DEFAULT ''"))
            if "destination_email" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_email VARCHAR(190) DEFAULT ''"))
            if "destination_state_code" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_state_code VARCHAR(10) DEFAULT ''"))
            if "destination_municipality_code" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_municipality_code VARCHAR(20) DEFAULT ''"))
            if "destination_postal_code" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_postal_code VARCHAR(10) DEFAULT ''"))
            if "destination_colony_id" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_colony_id VARCHAR(64) DEFAULT ''"))
            if "destination_address_line" not in party_columns:
                conn.execute(text("ALTER TABLE guide_parties ADD COLUMN destination_address_line VARCHAR(255) DEFAULT ''"))

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
        users = db.query(User).all()
        existing_links = {
            (item.user_id, item.role.value)
            for item in db.query(UserRoleLink).all()
        }
        for user in users:
            key = (user.id, user.role.value)
            if key not in existing_links:
                db.add(UserRoleLink(user_id=user.id, role=user.role))
        db.commit()
        try:
            sync_sepomex_catalog(db)
        except Exception:
            db.rollback()
            # Fallback to built-in catalog to keep bootstrap resilient without network.
            seed_geo_catalogs(db)
    finally:
        db.close()

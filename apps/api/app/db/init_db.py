from datetime import datetime, timezone

from app.db.base import Base
from app.db.geo_seed import seed_geo_catalogs
from app.db.models import QuotePolicyRule, User, UserRoleLink, ZoneSurchargeRule
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
            if "station_id" not in rider_columns:
                conn.execute(text("ALTER TABLE riders ADD COLUMN station_id VARCHAR(32)"))

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
        if "station_coverage_rules" not in tables:
            Base.metadata.tables["station_coverage_rules"].create(bind=engine, checkfirst=True)
        return

    lead_columns = {col["name"] for col in inspector.get_columns("contact_leads")}
    with engine.begin() as conn:
        if "status" not in lead_columns:
            conn.execute(text("ALTER TABLE contact_leads ADD COLUMN status VARCHAR(20) DEFAULT 'new'"))
            conn.execute(text("UPDATE contact_leads SET status = 'new' WHERE status IS NULL OR status = ''"))
        if "updated_at" not in lead_columns:
            conn.execute(text("ALTER TABLE contact_leads ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE"))
            conn.execute(text("UPDATE contact_leads SET updated_at = created_at WHERE updated_at IS NULL"))

    if "station_coverage_rules" not in tables:
        Base.metadata.tables["station_coverage_rules"].create(bind=engine, checkfirst=True)


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

        has_quote_rules = db.query(QuotePolicyRule.id).first() is not None
        if not has_quote_rules:
            now = datetime.now(timezone.utc)
            db.add_all(
                [
                    QuotePolicyRule(
                        service_type="programado",
                        service_factor=1.0,
                        active=True,
                        valid_from=now,
                        notes="Semilla inicial",
                    ),
                    QuotePolicyRule(
                        service_type="express",
                        service_factor=1.3,
                        active=True,
                        valid_from=now,
                        notes="Semilla inicial",
                    ),
                    QuotePolicyRule(
                        service_type="recurrente",
                        service_factor=0.9,
                        active=True,
                        valid_from=now,
                        notes="Semilla inicial",
                    ),
                    QuotePolicyRule(
                        service_type="mandaditos",
                        fallback_service_type="paqueteria",
                        max_distance_km=10.0,
                        service_factor=1.12,
                        active=True,
                        valid_from=now,
                        notes="Semilla inicial",
                    ),
                    QuotePolicyRule(
                        service_type="paqueteria",
                        service_factor=1.2,
                        active=True,
                        valid_from=now,
                        notes="Semilla inicial",
                    ),
                ]
            )

        has_zone_rules = db.query(ZoneSurchargeRule.id).first() is not None
        if not has_zone_rules:
            now = datetime.now(timezone.utc)
            db.add_all(
                [
                    ZoneSurchargeRule(zone_type="urbana", zone_factor=1.0, complexity_factor=1.0, eta_extra_minutes=0, active=True, valid_from=now, notes="Semilla inicial"),
                    ZoneSurchargeRule(zone_type="metropolitana", zone_factor=1.18, complexity_factor=1.0, eta_extra_minutes=0, active=True, valid_from=now, notes="Semilla inicial"),
                    ZoneSurchargeRule(zone_type="intermunicipal", zone_factor=1.35, complexity_factor=1.0, eta_extra_minutes=18, active=True, valid_from=now, notes="Semilla inicial"),
                    ZoneSurchargeRule(zone_type="rural", rural_complexity="baja", zone_factor=1.45, complexity_factor=1.04, eta_extra_minutes=28, active=True, valid_from=now, notes="Semilla inicial"),
                    ZoneSurchargeRule(zone_type="rural", rural_complexity="media", zone_factor=1.45, complexity_factor=1.12, eta_extra_minutes=28, active=True, valid_from=now, notes="Semilla inicial"),
                    ZoneSurchargeRule(zone_type="rural", rural_complexity="alta", zone_factor=1.45, complexity_factor=1.25, eta_extra_minutes=28, active=True, valid_from=now, notes="Semilla inicial"),
                ]
            )

        db.commit()
        try:
            sync_sepomex_catalog(db)
        except Exception:
            db.rollback()
            # Fallback to built-in catalog to keep bootstrap resilient without network.
            seed_geo_catalogs(db)
    finally:
        db.close()

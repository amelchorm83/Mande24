from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.security import hash_password
from app.db.models import CommissionClose, Guide, Rider, RouteLeg, RouteLegStatusChange, User, UserRole
from app.db.session import SessionLocal
from app.services.commissions import close_weekly_commissions


def _ensure_admin(db):
    email = "smoke.stagea.admin@mande24.test"
    password = "SmokeAdmin123*"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name="Smoke Stage A Admin",
            password_hash=hash_password(password),
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        db.flush()
    return user, email, password


def _ensure_rider(db):
    email = "smoke.stagea.rider@mande24.test"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name="Smoke Stage A Rider",
            password_hash=hash_password("SmokeRider123*"),
            role=UserRole.rider,
            is_active=True,
        )
        db.add(user)
        db.flush()

    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        rider = Rider(user_id=user.id, active=True, is_available=True)
        db.add(rider)
        db.flush()
    return rider


def _create_route_leg_candidate(db):
    guide = Guide(
        guide_code=f"SMOKE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        customer_name="Smoke Stage A",
        destination_name="Smoke Stage A Dest",
        service_type="package",
        sale_amount=0.0,
        currency="MXN",
    )
    db.add(guide)
    db.flush()

    route_leg = RouteLeg(
        guide_id=guide.id,
        sequence=1,
        leg_type="pickup_to_client",
        from_node_type="client_origin",
        to_node_type="client_destination",
        status="planned",
    )
    db.add(route_leg)
    db.flush()
    return guide, route_leg


def main():
    db = SessionLocal()
    try:
        admin, admin_email, admin_password = _ensure_admin(db)
        rider = _ensure_rider(db)
        _guide, route_leg = _create_route_leg_candidate(db)
        audit_rows_before = db.query(RouteLegStatusChange).count()
        db.commit()

        # Validate idempotency contract.
        first = close_weekly_commissions(db)
        second = close_weekly_commissions(db)
        close_rows = db.query(CommissionClose).count()

        result = {
            "admin_user_id": admin.id,
            "admin_email": admin_email,
            "admin_password": admin_password,
            "route_leg_id": route_leg.id,
            "rider_id": rider.id,
            "close_first": first,
            "close_second": second,
            "commission_close_rows": close_rows,
            "audit_rows_before": audit_rows_before,
        }
        print(json.dumps(result, ensure_ascii=True))
    finally:
        db.close()


if __name__ == "__main__":
    main()

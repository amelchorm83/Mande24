import os
from uuid import uuid4

TEST_DB_PATH = f"./test_mande24_{uuid4().hex}.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test_secret"

from fastapi.testclient import TestClient

from app.db.models import Delivery, GeoColony, RiderCommission, StationCommission
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.main import app

init_db()

client = TestClient(app)


def _ensure_minimal_geo_data() -> None:
    db = SessionLocal()
    try:
        state = db.query(GeoColony).first()
        if state:
            return

        from app.db.models import GeoMunicipality, GeoPostalCode, GeoState

        if not db.query(GeoState).filter(GeoState.code == "SIN").first():
            db.add(GeoState(code="SIN", name="Sinaloa"))

        if not db.query(GeoMunicipality).filter(GeoMunicipality.code == "SIN001").first():
            db.add(GeoMunicipality(code="SIN001", state_code="SIN", name="Ahome"))

        if not db.query(GeoPostalCode).filter(GeoPostalCode.code == "81200").first():
            db.add(GeoPostalCode(code="81200", municipality_code="SIN001", settlement="Centro"))

        if not db.query(GeoColony).filter(GeoColony.id == "SIN001-81200-CENTRO").first():
            db.add(
                GeoColony(
                    id="SIN001-81200-CENTRO",
                    state_code="SIN",
                    municipality_code="SIN001",
                    postal_code="81200",
                    name="Centro",
                    settlement_type="Colonia",
                    sepomex_code="0001",
                )
            )

        db.commit()
    finally:
        db.close()


def _auth_headers(email: str, role: str) -> dict[str, str]:
    password = "Secret123"
    register_payload = {
        "email": email,
        "full_name": email.split("@")[0],
        "password": password,
        "role": role,
    }
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code in (200, 409)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _erp_session_cookies(email: str, role: str) -> dict[str, str]:
    password = "Secret123"
    register_payload = {
        "email": email,
        "full_name": email.split("@")[0],
        "password": password,
        "role": role,
    }
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code in (200, 409)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {
        "m24_erp_token": token,
        "m24_erp_active_role": role,
        "m24_erpmande24_user_email": email,
    }


def _create_catalog_data(admin_headers: dict[str, str]) -> tuple[str, str, str]:
    client.post("/api/v1/catalogs/zones", json={"name": "Centro", "code": "CTR"}, headers=admin_headers)
    zones_response = client.get("/api/v1/catalogs/zones", headers=admin_headers)
    zone_id = zones_response.json()[0]["id"]

    client.post(
        "/api/v1/catalogs/services",
        json={"name": "Mensajeria Express", "service_type": "messaging"},
        headers=admin_headers,
    )
    services_response = client.get("/api/v1/catalogs/services", headers=admin_headers)
    service_id = services_response.json()[0]["id"]

    client.post(
        "/api/v1/catalogs/stations",
        json={"name": "Estacion Centro", "zone_id": zone_id},
        headers=admin_headers,
    )
    stations_response = client.get("/api/v1/catalogs/stations", headers=admin_headers)
    station_id = stations_response.json()[0]["id"]

    client.post(
        "/api/v1/catalogs/pricing-rules",
        json={
            "service_id": service_id,
            "station_id": station_id,
            "price": 120.0,
            "currency": "MXN",
        },
        headers=admin_headers,
    )
    return service_id, station_id, zone_id


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_fetch_guide() -> None:
    admin_headers = _auth_headers("admin.demo@mande24.test", "admin")
    service_id, station_id, _zone_id = _create_catalog_data(admin_headers)

    headers = _auth_headers("cliente.demo@mande24.test", "client")

    payload = {
        "customer_name": "Cliente Demo",
        "destination_name": "Destino Demo",
        "service_id": service_id,
        "station_id": station_id,
    }
    create_response = client.post("/api/v1/guides", json=payload, headers=headers)
    assert create_response.status_code == 200

    guide = create_response.json()
    assert guide["sale_amount"] == 120.0
    assert guide["currency"] == "MXN"

    deliveries_response = client.get(f"/api/v1/guides/{guide['guide_code']}/deliveries", headers=headers)
    assert deliveries_response.status_code == 200
    assert len(deliveries_response.json()) >= 1

    get_response = client.get(f"/api/v1/guides/{guide['guide_code']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["customer_name"] == "Cliente Demo"


def test_catalogs_admin_flow() -> None:
    headers = _auth_headers("admin2.demo@mande24.test", "admin")
    _service_id, _station_id, _zone_id = _create_catalog_data(headers)
    pricing_list = client.get("/api/v1/catalogs/pricing-rules", headers=headers)
    assert pricing_list.status_code == 200
    assert len(pricing_list.json()) >= 1


def test_weekly_commissions() -> None:
    admin_headers = _auth_headers("admin3.demo@mande24.test", "admin")
    service_id, station_id, zone_id = _create_catalog_data(admin_headers)
    _ensure_minimal_geo_data()

    geo_db = SessionLocal()
    try:
        colony = geo_db.query(GeoColony).first()
        assert colony is not None
        origin_state_code = colony.state_code
        origin_municipality_code = colony.municipality_code
        origin_postal_code = colony.postal_code
        origin_colony_id = colony.id
    finally:
        geo_db.close()

    client_headers = _auth_headers("cliente2.demo@mande24.test", "client")
    guide_payload = {
        "customer_name": "Cliente Comisiones",
        "destination_name": "Destino Comisiones",
        "service_id": service_id,
        "station_id": station_id,
        "origin_whatsapp_phone": "5511111111",
        "origin_email": "origin.demo@mande24.test",
        "origin_state_code": origin_state_code,
        "origin_municipality_code": origin_municipality_code,
        "origin_postal_code": origin_postal_code,
        "origin_colony_id": origin_colony_id,
        "origin_address_line": "Calle Origen 123",
        "destination_whatsapp_phone": "5522222222",
        "destination_email": "destination.demo@mande24.test",
        "destination_state_code": origin_state_code,
        "destination_municipality_code": origin_municipality_code,
        "destination_postal_code": origin_postal_code,
        "destination_colony_id": origin_colony_id,
        "destination_address_line": "Calle Destino 456",
    }
    create_response = client.post("/api/v1/guides", json=guide_payload, headers=client_headers)
    assert create_response.status_code == 200

    rider_user_email = "rider.demo@mande24.test"
    rider_headers = _auth_headers(rider_user_email, "rider")
    intruder_rider_email = "rider.unauthorized@mande24.test"
    intruder_rider_headers = _auth_headers(intruder_rider_email, "rider")
    rider_register = client.post(
        "/api/v1/auth/register",
        json={"email": rider_user_email, "full_name": "Rider Demo", "password": "Secret123", "role": "rider"},
    )
    assert rider_register.status_code in (200, 409)

    users_db = SessionLocal()
    try:
        from app.db.models import Rider, User

        rider_user = users_db.query(User).filter(User.email == rider_user_email).first()
        assert rider_user is not None

        existing_rider = users_db.query(Rider).filter(Rider.user_id == rider_user.id).first()
        if not existing_rider:
            create_rider_response = client.post(
                "/api/v1/catalogs/riders",
                json={"user_id": rider_user.id, "zone_id": zone_id, "vehicle_type": "motorcycle"},
                headers=admin_headers,
            )
            assert create_rider_response.status_code in (200, 409)

            rider = users_db.query(Rider).filter(Rider.user_id == rider_user.id).first()
            assert rider is not None
        else:
            rider = existing_rider

        intruder_user = users_db.query(User).filter(User.email == intruder_rider_email).first()
        assert intruder_user is not None
        intruder_rider = users_db.query(Rider).filter(Rider.user_id == intruder_user.id).first()
        if not intruder_rider:
            create_intruder_rider_response = client.post(
                "/api/v1/catalogs/riders",
                json={"user_id": intruder_user.id, "zone_id": zone_id, "vehicle_type": "motorcycle"},
                headers=admin_headers,
            )
            assert create_intruder_rider_response.status_code in (200, 409)

        guide_code = create_response.json()["guide_code"]
        guide_fetch = client.get(f"/api/v1/guides/{guide_code}", headers=client_headers)
        assert guide_fetch.status_code == 200

        route_legs_response = client.get(f"/api/v1/guides/{guide_code}/route-legs", headers=admin_headers)
        assert route_legs_response.status_code == 200
        route_legs = route_legs_response.json()
        assert len(route_legs) >= 1

        for leg in route_legs:
            assign_response = client.patch(
                f"/api/v1/guides/route-legs/{leg['id']}/assign",
                json={"rider_id": rider.id, "status": "assigned"},
                headers=admin_headers,
            )
            assert assign_response.status_code == 200

        rider_route_legs = client.get("/api/v1/guides/route-legs/my", headers=rider_headers)
        assert rider_route_legs.status_code == 200
        my_guide_legs = sorted(
            [item for item in rider_route_legs.json() if item["guide_code"] == guide_code],
            key=lambda item: item["sequence"],
        )
        assert len(my_guide_legs) == len(route_legs)

        for leg in my_guide_legs:
            in_progress_response = client.patch(
                f"/api/v1/guides/route-legs/{leg['id']}/assign",
                json={"status": "in_progress"},
                headers=rider_headers,
            )
            assert in_progress_response.status_code == 200

            completed_response = client.patch(
                f"/api/v1/guides/route-legs/{leg['id']}/assign",
                json={"status": "completed"},
                headers=rider_headers,
            )
            assert completed_response.status_code == 200

        delivery = users_db.query(Delivery).order_by(Delivery.created_at.desc()).first()
        assert delivery is not None
        delivery.rider_id = rider.id
        delivery.commission_amount = 35.0
        users_db.commit()
        delivery_id = delivery.id
    finally:
        users_db.close()

    unauthorized_stage_update = client.patch(
        f"/api/v1/guides/deliveries/{delivery_id}/stage",
        json={"stage": "delivered", "has_evidence": True, "has_signature": True},
        headers=intruder_rider_headers,
    )
    assert unauthorized_stage_update.status_code == 403

    stage_update = client.patch(
        f"/api/v1/guides/deliveries/{delivery_id}/stage",
        json={"stage": "delivered", "has_evidence": True, "has_signature": True},
        headers=rider_headers,
    )
    assert stage_update.status_code == 200

    invalid_week = client.get("/api/v1/commissions/riders/weekly?week_start=invalid-date", headers=admin_headers)
    assert invalid_week.status_code == 422

    rider_commissions = client.get("/api/v1/commissions/riders/weekly", headers=admin_headers)
    assert rider_commissions.status_code == 200
    assert len(rider_commissions.json()["rows"]) >= 1

    rider_by_leg = client.get("/api/v1/commissions/riders/weekly/by-leg", headers=admin_headers)
    assert rider_by_leg.status_code == 200
    rider_by_leg_rows = rider_by_leg.json()["rows"]
    assert len(rider_by_leg_rows) >= 1
    assert any(row["leg_count"] >= 1 for row in rider_by_leg_rows)

    close_rider_1 = client.post("/api/v1/commissions/riders/weekly/close", headers=admin_headers)
    assert close_rider_1.status_code == 200
    close_rider_2 = client.post("/api/v1/commissions/riders/weekly/close", headers=admin_headers)
    assert close_rider_2.status_code == 200

    station_commissions = client.get("/api/v1/commissions/stations/weekly", headers=admin_headers)
    assert station_commissions.status_code == 200
    assert len(station_commissions.json()["rows"]) >= 1

    station_by_leg = client.get("/api/v1/commissions/stations/weekly/by-leg", headers=admin_headers)
    assert station_by_leg.status_code == 200
    station_by_leg_rows = station_by_leg.json()["rows"]
    assert len(station_by_leg_rows) >= 1
    assert any(row["leg_count"] >= 1 for row in station_by_leg_rows)

    close_station_1 = client.post("/api/v1/commissions/stations/weekly/close", headers=admin_headers)
    assert close_station_1.status_code == 200
    close_station_2 = client.post("/api/v1/commissions/stations/weekly/close", headers=admin_headers)
    assert close_station_2.status_code == 200

    rider_history = client.get("/api/v1/commissions/riders/weekly/history", headers=admin_headers)
    assert rider_history.status_code == 200
    assert len(rider_history.json()) >= 1

    station_history = client.get("/api/v1/commissions/stations/weekly/history", headers=admin_headers)
    assert station_history.status_code == 200
    assert len(station_history.json()) >= 1

    verify_db = SessionLocal()
    try:
        rider_snapshots = verify_db.query(RiderCommission).all()
        station_snapshots = verify_db.query(StationCommission).all()
        assert len(rider_snapshots) >= 1
        assert len(station_snapshots) >= 1
    finally:
        verify_db.close()


def test_backend_ui_role_guards() -> None:
    station_cookies = _erp_session_cookies("erp.station.demo@mande24.test", "station")
    rider_cookies = _erp_session_cookies("erp.rider.demo@mande24.test", "rider")

    service_block = client.post(
        "/ERPMande24/catalogs/services/bulk-toggle",
        data={"active": "true"},
        cookies=station_cookies,
        follow_redirects=False,
    )
    assert service_block.status_code == 303
    assert "Sin+permisos+para+editar+servicios+con+rol+station" in (service_block.headers.get("location") or "")

    rider_block = client.post(
        "/ERPMande24/guides/create",
        data={"customer_name": "A", "destination_name": "B", "service_id": "fake", "station_id": "fake"},
        cookies=rider_cookies,
        follow_redirects=False,
    )
    assert rider_block.status_code == 303
    assert "Sin+permisos+para+crear+guia+con+rol+rider" in (rider_block.headers.get("location") or "")

    station_ops = client.post(
        "/ERPMande24/guides/create",
        data={"customer_name": "A", "destination_name": "B", "service_id": "fake", "station_id": "fake"},
        cookies=station_cookies,
        follow_redirects=False,
    )
    assert station_ops.status_code == 303
    assert "Sin+permisos" not in (station_ops.headers.get("location") or "")


def test_backend_ui_pagination_and_timeline() -> None:
    admin_cookies = _erp_session_cookies("erp.admin.demo@mande24.test", "admin")

    seed_response = client.post("/ERPMande24/demo/seed")
    assert seed_response.status_code == 200
    seed = seed_response.json()

    for idx in range(23):
        created = client.post(
            "/ERPMande24/guides/create",
            data={
                "customer_name": f"Cliente {idx}",
                "destination_name": f"Destino {idx}",
                "service_id": seed["service_id"],
                "station_id": seed["station_id"],
            },
            cookies=admin_cookies,
            follow_redirects=False,
        )
        assert created.status_code == 303

    guides_page = client.get("/ERPMande24/guides?page=2&page_size=10")
    assert guides_page.status_code == 200
    assert "Pagina 2 de 3" in guides_page.text
    assert "page=1&page_size=10" in guides_page.text
    assert "page=3&page_size=10" in guides_page.text

    db = SessionLocal()
    try:
        latest_guide = db.query(Delivery).order_by(Delivery.created_at.desc()).first()
        assert latest_guide is not None
        guide_code = latest_guide.guide.guide_code
    finally:
        db.close()

    guide_detail = client.get(f"/ERPMande24/guides/{guide_code}")
    assert guide_detail.status_code == 200
    assert "<h3>Timeline</h3>" in guide_detail.text

    delivery_detail = client.get(f"/ERPMande24/deliveries/{latest_guide.id}")
    assert delivery_detail.status_code == 200
    assert "<h3>Timeline</h3>" in delivery_detail.text

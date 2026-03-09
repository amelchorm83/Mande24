import os

TEST_DB_PATH = "./test_mande24.db"
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test_secret"

from fastapi.testclient import TestClient

from app.db.models import Delivery, RiderCommission, StationCommission
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.main import app

init_db()

client = TestClient(app)


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

    client_headers = _auth_headers("cliente2.demo@mande24.test", "client")
    guide_payload = {
        "customer_name": "Cliente Comisiones",
        "destination_name": "Destino Comisiones",
        "service_id": service_id,
        "station_id": station_id,
    }
    create_response = client.post("/api/v1/guides", json=guide_payload, headers=client_headers)
    assert create_response.status_code == 200

    rider_user_email = "rider.demo@mande24.test"
    rider_headers = _auth_headers(rider_user_email, "rider")
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

        guide_code = create_response.json()["guide_code"]
        guide_fetch = client.get(f"/api/v1/guides/{guide_code}", headers=client_headers)
        assert guide_fetch.status_code == 200

        delivery = users_db.query(Delivery).order_by(Delivery.created_at.desc()).first()
        assert delivery is not None

        rider = users_db.query(Rider).filter(Rider.user_id == rider_user.id).first()
        assert rider is not None
        delivery.rider_id = rider.id
        delivery.commission_amount = 35.0
        users_db.commit()
        delivery_id = delivery.id
    finally:
        users_db.close()

    stage_update = client.patch(
        f"/api/v1/guides/deliveries/{delivery_id}/stage",
        json={"stage": "delivered", "has_evidence": True, "has_signature": True},
        headers=rider_headers,
    )
    assert stage_update.status_code == 200

    rider_commissions = client.get("/api/v1/commissions/riders/weekly", headers=admin_headers)
    assert rider_commissions.status_code == 200
    assert len(rider_commissions.json()["rows"]) >= 1

    close_rider_1 = client.post("/api/v1/commissions/riders/weekly/close", headers=admin_headers)
    assert close_rider_1.status_code == 200
    close_rider_2 = client.post("/api/v1/commissions/riders/weekly/close", headers=admin_headers)
    assert close_rider_2.status_code == 200

    station_commissions = client.get("/api/v1/commissions/stations/weekly", headers=admin_headers)
    assert station_commissions.status_code == 200
    assert len(station_commissions.json()["rows"]) >= 1

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
    service_block = client.post(
        "/ERPMande24/catalogs/services/bulk-toggle",
        data={"active": "true"},
        cookies={"m24_erpmande24_role": "station"},
        follow_redirects=False,
    )
    assert service_block.status_code == 303
    assert "Sin+permisos+para+editar+servicios+con+rol+station" in (service_block.headers.get("location") or "")

    rider_block = client.post(
        "/ERPMande24/guides/create",
        data={"customer_name": "A", "destination_name": "B", "service_id": "fake", "station_id": "fake"},
        cookies={"m24_erpmande24_role": "rider"},
        follow_redirects=False,
    )
    assert rider_block.status_code == 303
    assert "Sin+permisos+para+crear+guia+con+rol+rider" in (rider_block.headers.get("location") or "")

    station_ops = client.post(
        "/ERPMande24/guides/create",
        data={"customer_name": "A", "destination_name": "B", "service_id": "fake", "station_id": "fake"},
        cookies={"m24_erpmande24_role": "station"},
        follow_redirects=False,
    )
    assert station_ops.status_code == 303
    assert "Sin+permisos" not in (station_ops.headers.get("location") or "")


def test_backend_ui_pagination_and_timeline() -> None:
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
            cookies={"m24_erpmande24_role": "admin"},
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

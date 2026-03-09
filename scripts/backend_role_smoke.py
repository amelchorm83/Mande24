from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)
    cases = [
        (
            "ADMIN_MANAGE",
            "/ERPMande24/catalogs/services/bulk-toggle",
            {"active": "true"},
            {"m24_erpmande24_role": "admin"},
        ),
        (
            "STATION_MANAGE",
            "/ERPMande24/catalogs/services/bulk-toggle",
            {"active": "true"},
            {"m24_erpmande24_role": "station"},
        ),
        (
            "STATION_OPS",
            "/ERPMande24/guides/create",
            {
                "customer_name": "A",
                "destination_name": "B",
                "service_id": "fake",
                "station_id": "fake",
            },
            {"m24_erpmande24_role": "station"},
        ),
        (
            "RIDER_OPS",
            "/ERPMande24/guides/create",
            {
                "customer_name": "A",
                "destination_name": "B",
                "service_id": "fake",
                "station_id": "fake",
            },
            {"m24_erpmande24_role": "rider"},
        ),
        (
            "CLIENT_OPS_DELIVERY",
            "/ERPMande24/deliveries/stage",
            {"delivery_id": "fake", "stage": "assigned"},
            {"m24_erpmande24_role": "client"},
        ),
        (
            "ADMIN_OPS_DELIVERY",
            "/ERPMande24/deliveries/stage",
            {"delivery_id": "fake", "stage": "assigned"},
            {"m24_erpmande24_role": "admin"},
        ),
    ]

    for name, path, payload, cookies in cases:
        response = client.post(path, data=payload, cookies=cookies, follow_redirects=False)
        location = response.headers.get("location", "")
        print(f"{name}|STATUS={response.status_code}|LOC={location}")


if __name__ == "__main__":
    main()

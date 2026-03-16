from app.db.models import GeoColony, GeoMunicipality, GeoPostalCode, GeoState
from app.db.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        state = db.query(GeoState).filter(GeoState.code == "SIN").first()
        if not state:
            state = GeoState(code="SIN", name="Sinaloa")
            db.add(state)

        municipality = db.query(GeoMunicipality).filter(GeoMunicipality.code == "SIN001").first()
        if not municipality:
            municipality = GeoMunicipality(code="SIN001", state_code="SIN", name="Ahome")
            db.add(municipality)

        postal = db.query(GeoPostalCode).filter(GeoPostalCode.code == "81200").first()
        if not postal:
            postal = GeoPostalCode(code="81200", municipality_code="SIN001", settlement="Centro")
            db.add(postal)

        colony = db.query(GeoColony).filter(GeoColony.id == "SIN001-81200-CENTRO").first()
        if not colony:
            colony = GeoColony(
                id="SIN001-81200-CENTRO",
                state_code="SIN",
                municipality_code="SIN001",
                postal_code="81200",
                name="Centro",
                settlement_type="Colonia",
                sepomex_code="0001",
            )
            db.add(colony)

        db.commit()
        print("SMOKE_GEO_READY")
    finally:
        db.close()


if __name__ == "__main__":
    main()

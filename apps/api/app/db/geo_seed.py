from app.db.models import GeoColony, GeoMunicipality, GeoPostalCode, GeoState

# Base bootstrap catalog for MX states with representative municipality/postal code.
# The structure supports loading a larger official catalog later without code changes.
GEO_SEED_ROWS = [
    ("AGS", "Aguascalientes", "AGS-001", "Aguascalientes", "20000", "Zona Centro"),
    ("BCN", "Baja California", "BCN-001", "Mexicali", "21000", "Centro Civico"),
    ("BCS", "Baja California Sur", "BCS-001", "La Paz", "23000", "Centro"),
    ("CAM", "Campeche", "CAM-001", "Campeche", "24000", "Centro"),
    ("CHP", "Chiapas", "CHP-001", "Tuxtla Gutierrez", "29000", "Centro"),
    ("CHH", "Chihuahua", "CHH-001", "Chihuahua", "31000", "Centro"),
    ("CMX", "Ciudad de Mexico", "CMX-001", "Cuauhtemoc", "06000", "Centro"),
    ("COA", "Coahuila", "COA-001", "Saltillo", "25000", "Centro"),
    ("COL", "Colima", "COL-001", "Colima", "28000", "Centro"),
    ("DUR", "Durango", "DUR-001", "Durango", "34000", "Centro"),
    ("MEX", "Estado de Mexico", "MEX-001", "Toluca", "50000", "Centro"),
    ("GTO", "Guanajuato", "GTO-001", "Guanajuato", "36000", "Centro"),
    ("GRO", "Guerrero", "GRO-001", "Chilpancingo", "39000", "Centro"),
    ("HID", "Hidalgo", "HID-001", "Pachuca", "42000", "Centro"),
    ("JAL", "Jalisco", "JAL-001", "Guadalajara", "44100", "Centro"),
    ("MIC", "Michoacan", "MIC-001", "Morelia", "58000", "Centro"),
    ("MOR", "Morelos", "MOR-001", "Cuernavaca", "62000", "Centro"),
    ("NAY", "Nayarit", "NAY-001", "Tepic", "63000", "Centro"),
    ("NLE", "Nuevo Leon", "NLE-001", "Monterrey", "64000", "Centro"),
    ("OAX", "Oaxaca", "OAX-001", "Oaxaca de Juarez", "68000", "Centro"),
    ("PUE", "Puebla", "PUE-001", "Puebla", "72000", "Centro"),
    ("QUE", "Queretaro", "QUE-001", "Queretaro", "76000", "Centro"),
    ("ROO", "Quintana Roo", "ROO-001", "Chetumal", "77000", "Centro"),
    ("SLP", "San Luis Potosi", "SLP-001", "San Luis Potosi", "78000", "Centro"),
    ("SIN", "Sinaloa", "SIN-001", "Culiacan", "80000", "Centro"),
    ("SON", "Sonora", "SON-001", "Hermosillo", "83000", "Centro"),
    ("TAB", "Tabasco", "TAB-001", "Villahermosa", "86000", "Centro"),
    ("TAM", "Tamaulipas", "TAM-001", "Ciudad Victoria", "87000", "Centro"),
    ("TLA", "Tlaxcala", "TLA-001", "Tlaxcala", "90000", "Centro"),
    ("VER", "Veracruz", "VER-001", "Xalapa", "91000", "Centro"),
    ("YUC", "Yucatan", "YUC-001", "Merida", "97000", "Centro"),
    ("ZAC", "Zacatecas", "ZAC-001", "Zacatecas", "98000", "Centro"),
]


def seed_geo_catalogs(db) -> None:
    if db.query(GeoState).first() and db.query(GeoColony).first():
        return

    state_codes = {row[0] for row in db.query(GeoState.code).all()}
    municipality_codes = {row[0] for row in db.query(GeoMunicipality.code).all()}
    postal_codes = {row[0] for row in db.query(GeoPostalCode.code).all()}
    colony_ids = {row[0] for row in db.query(GeoColony.id).all()}

    for state_code, state_name, _municipality_code, _municipality_name, _postal_code, _settlement in GEO_SEED_ROWS:
        if state_code not in state_codes:
            db.add(GeoState(code=state_code, name=state_name))
            state_codes.add(state_code)
    db.flush()

    for state_code, _state_name, municipality_code, municipality_name, _postal_code, _settlement in GEO_SEED_ROWS:
        if municipality_code not in municipality_codes:
            db.add(GeoMunicipality(code=municipality_code, state_code=state_code, name=municipality_name))
            municipality_codes.add(municipality_code)
    db.flush()

    for _state_code, _state_name, municipality_code, _municipality_name, postal_code, settlement in GEO_SEED_ROWS:
        if postal_code not in postal_codes:
            db.add(GeoPostalCode(code=postal_code, municipality_code=municipality_code, settlement=settlement))
            postal_codes.add(postal_code)

    db.flush()

    for state_code, _state_name, municipality_code, _municipality_name, postal_code, settlement in GEO_SEED_ROWS:
        colony_id = f"{postal_code}:{municipality_code}"
        if colony_id not in colony_ids:
            db.add(
                GeoColony(
                    id=colony_id,
                    state_code=state_code,
                    municipality_code=municipality_code,
                    postal_code=postal_code,
                    name=settlement,
                    settlement_type="Colonia",
                    sepomex_code=municipality_code,
                )
            )
            colony_ids.add(colony_id)

    db.commit()

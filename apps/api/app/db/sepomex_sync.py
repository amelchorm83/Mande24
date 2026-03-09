from __future__ import annotations

from datetime import date, datetime, timezone
import io
import re
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
import zipfile

from sqlalchemy.orm import Session

from app.db.models import GeoCatalogSync, GeoColony, GeoMunicipality, GeoPostalCode, GeoState

SEPOMEX_PAGE_URL = "https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/CodigoPostal_Exportar.aspx"
SYNC_META_KEY = "sepomex_last_sync"

# Canonical state codes already used by the app. SEPOMEX numeric state ids are mapped to these where possible.
STATE_NAME_TO_CODE = {
    "aguascalientes": "AGS",
    "baja california": "BCN",
    "baja california sur": "BCS",
    "campeche": "CAM",
    "chiapas": "CHP",
    "chihuahua": "CHH",
    "ciudad de mexico": "CMX",
    "coahuila": "COA",
    "colima": "COL",
    "durango": "DUR",
    "estado de mexico": "MEX",
    "guanajuato": "GTO",
    "guerrero": "GRO",
    "hidalgo": "HID",
    "jalisco": "JAL",
    "michoacan": "MIC",
    "morelos": "MOR",
    "nayarit": "NAY",
    "nuevo leon": "NLE",
    "oaxaca": "OAX",
    "puebla": "PUE",
    "queretaro": "QUE",
    "quintana roo": "ROO",
    "san luis potosi": "SLP",
    "sinaloa": "SIN",
    "sonora": "SON",
    "tabasco": "TAB",
    "tamaulipas": "TAM",
    "tlaxcala": "TLA",
    "veracruz": "VER",
    "yucatan": "YUC",
    "zacatecas": "ZAC",
}


def _norm(value: str) -> str:
    text = (value or "").strip().lower()
    text = text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    return text


def _norm_col_name(value: str) -> str:
    return (value or "").strip().lstrip("\ufeff").lower()


def _hidden_value(page_html: str, name: str) -> str:
    pattern = rf'name="{re.escape(name)}"\s+id="{re.escape(name)}"\s+value="([^"]*)"'
    match = re.search(pattern, page_html, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def _download_sepomex_zip() -> tuple[bytes, str]:
    opener = build_opener(HTTPCookieProcessor())
    get_req = Request(
        SEPOMEX_PAGE_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with opener.open(get_req, timeout=60) as response:
        page_html = response.read().decode("utf-8", errors="ignore")

    view_state = _hidden_value(page_html, "__VIEWSTATE")
    event_validation = _hidden_value(page_html, "__EVENTVALIDATION")
    view_state_generator = _hidden_value(page_html, "__VIEWSTATEGENERATOR")
    date_match = re.search(r"Ultima\s+Actualizacion[:\s]+(\d{2}/\d{2}/\d{4})", page_html, flags=re.IGNORECASE)
    if not date_match:
        date_match = re.search(r"Última\s+Actualización[:\s]+(\d{2}/\d{2}/\d{4})", page_html, flags=re.IGNORECASE)
    catalog_date = date_match.group(1) if date_match else ""

    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": view_state,
        "__VIEWSTATEGENERATOR": view_state_generator,
        "__EVENTVALIDATION": event_validation,
        "cboEdo": "00",
        "rblTipo": "txt",
        "btnDescarga.x": "20",
        "btnDescarga.y": "12",
    }

    post_req = Request(
        SEPOMEX_PAGE_URL,
        data=urlencode(payload).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": SEPOMEX_PAGE_URL,
            "Accept": "*/*",
        },
    )
    with opener.open(post_req, timeout=120) as response:
        blob = response.read()

    if not blob.startswith(b"PK"):
        raise RuntimeError("SEPOMEX download did not return ZIP content")
    return blob, catalog_date


def sync_sepomex_catalog(db: Session, force: bool = False) -> bool:
    sync_row = db.query(GeoCatalogSync).filter(GeoCatalogSync.key == SYNC_META_KEY).first()
    today = date.today().isoformat()
    if sync_row and sync_row.value == today and not force:
        return False

    zip_bytes, catalog_date = _download_sepomex_zip()

    states_by_code = {item.code: item for item in db.query(GeoState).all()}
    municipalities_by_code = {item.code: item for item in db.query(GeoMunicipality).all()}
    postal_by_code = {item.code: item for item in db.query(GeoPostalCode).all()}
    existing_colony_ids = {row[0] for row in db.query(GeoColony.id).all()}

    new_states: list[GeoState] = []
    new_municipalities: list[GeoMunicipality] = []
    new_postals: list[GeoPostalCode] = []
    new_colonies: list[GeoColony] = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        txt_name = next((name for name in archive.namelist() if name.lower().endswith(".txt")), "")
        if not txt_name:
            raise RuntimeError("SEPOMEX ZIP has no TXT payload")

        with archive.open(txt_name) as raw_file:
            stream = io.TextIOWrapper(raw_file, encoding="latin-1", errors="ignore")
            idx = {}
            scanned_lines: list[str] = []
            for _ in range(60):
                line = stream.readline()
                if not line:
                    break
                clean = line.strip()
                if not clean:
                    continue
                scanned_lines.append(clean)
                columns = clean.split("|")
                maybe_idx = {_norm_col_name(name): i for i, name in enumerate(columns)}
                if "d_codigo" in maybe_idx and "d_asenta" in maybe_idx:
                    idx = maybe_idx
                    break

            required = ["d_codigo", "d_asenta", "d_tipo_asenta", "d_mnpio", "d_estado", "id_asenta_cpcons", "c_mnpio"]
            if any(key not in idx for key in required):
                preview = " | ".join(scanned_lines[:3]) if scanned_lines else "<empty>"
                raise RuntimeError(f"SEPOMEX TXT format changed: required columns not found. Preview: {preview}")

            for line in stream:
                raw = line.strip()
                if not raw:
                    continue
                parts = raw.split("|")
                if len(parts) < len(columns):
                    continue

                state_name = parts[idx["d_estado"]].strip()
                state_key = _norm(state_name)
                state_code = STATE_NAME_TO_CODE.get(state_key)
                if not state_code:
                    # Match SEPOMEX verbose names like "coahuila de zaragoza" to existing canonical state names.
                    for existing_code, existing_state in states_by_code.items():
                        existing_key = _norm(existing_state.name)
                        if existing_key and (existing_key in state_key or state_key in existing_key):
                            state_code = existing_code
                            break
                if not state_code:
                    raw_state_num = parts[idx["c_estado"]].strip() if "c_estado" in idx else ""
                    state_code = raw_state_num.zfill(2) if raw_state_num else state_name[:3].upper()

                municipality_num = parts[idx["c_mnpio"]].strip().zfill(3)
                municipality_name = parts[idx["d_mnpio"]].strip()
                municipality_code = f"{state_code}-{municipality_num}"

                postal_code = parts[idx["d_codigo"]].strip().zfill(5)
                colony_name = parts[idx["d_asenta"]].strip()
                settlement_type = parts[idx["d_tipo_asenta"]].strip()
                sepomex_colony = parts[idx["id_asenta_cpcons"]].strip()
                colony_id = f"{postal_code}:{sepomex_colony or colony_name[:20]}"

                if state_code not in states_by_code:
                    state = GeoState(code=state_code, name=state_name)
                    states_by_code[state_code] = state
                    new_states.append(state)
                else:
                    if state_name and states_by_code[state_code].name != state_name:
                        states_by_code[state_code].name = state_name

                if municipality_code not in municipalities_by_code:
                    municipality = GeoMunicipality(code=municipality_code, state_code=state_code, name=municipality_name)
                    municipalities_by_code[municipality_code] = municipality
                    new_municipalities.append(municipality)

                if postal_code not in postal_by_code:
                    postal = GeoPostalCode(code=postal_code, municipality_code=municipality_code, settlement=colony_name)
                    postal_by_code[postal_code] = postal
                    new_postals.append(postal)

                if colony_id not in existing_colony_ids:
                    new_colonies.append(
                        GeoColony(
                            id=colony_id,
                            state_code=state_code,
                            municipality_code=municipality_code,
                            postal_code=postal_code,
                            name=colony_name,
                            settlement_type=settlement_type,
                            sepomex_code=sepomex_colony,
                        )
                    )
                    existing_colony_ids.add(colony_id)

    if new_states:
        db.add_all(new_states)
    if new_municipalities:
        db.add_all(new_municipalities)
    if new_postals:
        db.add_all(new_postals)

    # Ensure FK parent rows exist before colony inserts.
    db.flush()

    if new_colonies:
        chunk = 5000
        for start in range(0, len(new_colonies), chunk):
            db.add_all(new_colonies[start : start + chunk])
            db.flush()

    if not sync_row:
        sync_row = GeoCatalogSync(key=SYNC_META_KEY, value=today, updated_at=datetime.now(timezone.utc))
        db.add(sync_row)
    else:
        sync_row.value = today
        sync_row.updated_at = datetime.now(timezone.utc)

    if catalog_date:
        marker = db.query(GeoCatalogSync).filter(GeoCatalogSync.key == "sepomex_catalog_date").first()
        if not marker:
            marker = GeoCatalogSync(key="sepomex_catalog_date", value=catalog_date, updated_at=datetime.now(timezone.utc))
            db.add(marker)
        else:
            marker.value = catalog_date
            marker.updated_at = datetime.now(timezone.utc)

    db.commit()
    return True

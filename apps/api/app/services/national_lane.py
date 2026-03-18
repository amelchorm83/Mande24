from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import settings

# Canonical 3-letter codes mapped to macro-regions for nationwide pricing in Mexico.
STATE_TO_REGION = {
    "AGU": "centro",  # Aguascalientes
    "BCN": "noroeste",  # Baja California
    "BCS": "noroeste",  # Baja California Sur
    "CAM": "sureste",  # Campeche
    "CHP": "sur",  # Chiapas
    "CHH": "norte",  # Chihuahua
    "CMX": "centro",  # Ciudad de Mexico
    "COA": "noreste",  # Coahuila
    "COL": "occidente",  # Colima
    "DUR": "norte",  # Durango
    "GUA": "bajio",  # Guanajuato
    "GRO": "sur",  # Guerrero
    "HID": "centro",  # Hidalgo
    "JAL": "occidente",  # Jalisco
    "MEX": "centro",  # Estado de Mexico
    "MIC": "occidente",  # Michoacan
    "MOR": "centro",  # Morelos
    "NAY": "occidente",  # Nayarit
    "NLE": "noreste",  # Nuevo Leon
    "OAX": "sur",  # Oaxaca
    "PUE": "centro",  # Puebla
    "QUE": "bajio",  # Queretaro
    "ROO": "sureste",  # Quintana Roo
    "SLP": "bajio",  # San Luis Potosi
    "SIN": "noroeste",  # Sinaloa
    "SON": "noroeste",  # Sonora
    "TAB": "sureste",  # Tabasco
    "TAM": "noreste",  # Tamaulipas
    "TLA": "centro",  # Tlaxcala
    "VER": "golfo",  # Veracruz
    "YUC": "sureste",  # Yucatan
    "ZAC": "bajio",  # Zacatecas
}

STATE_ALIASES = {
    "AGS": "AGU",
    "CDMX": "CMX",
    "DF": "CMX",
    "QRO": "QUE",
    "QROO": "ROO",
    "NL": "NLE",
    "MICH": "MIC",
    "EDOMEX": "MEX",
    "ESTADODEMEXICO": "MEX",
    "CIUDADDEMEXICO": "CMX",
}


@dataclass
class NationalLaneDecision:
    origin_state_code: str
    destination_state_code: str
    origin_region_code: str | None
    destination_region_code: str | None
    lane_factor: float
    notes: list[str] = field(default_factory=list)


def _normalize_token(value: str | None) -> str:
    normalized = (value or "").strip().upper().replace(" ", "")
    if not normalized:
        return ""
    return STATE_ALIASES.get(normalized, normalized)


def resolve_region_code(state_code: str | None) -> str | None:
    canonical_state = _normalize_token(state_code)
    if not canonical_state:
        return None
    return STATE_TO_REGION.get(canonical_state)


def resolve_national_lane(
    *,
    origin_state_code: str | None,
    destination_state_code: str | None,
    origin_region_code: str | None = None,
    destination_region_code: str | None = None,
    origin_zone_code: str | None = None,
    destination_zone_code: str | None = None,
    use_station_handoff: bool = False,
) -> NationalLaneDecision:
    origin_state = _normalize_token(origin_state_code)
    destination_state = _normalize_token(destination_state_code)

    resolved_origin_region = _normalize_token(origin_region_code) or (resolve_region_code(origin_state) or None)
    resolved_destination_region = _normalize_token(destination_region_code) or (resolve_region_code(destination_state) or None)

    lane_factor = 1.0
    notes: list[str] = []

    if origin_state and destination_state and origin_state == destination_state:
        lane_factor *= settings.national_same_state_factor
        notes.append(f"Carril intrastatal {origin_state} con factor {settings.national_same_state_factor:.2f}.")
    elif origin_state and destination_state and origin_state != destination_state:
        lane_factor *= settings.national_cross_state_factor
        notes.append(
            f"Carril interestatal {origin_state}->{destination_state} con factor {settings.national_cross_state_factor:.2f}."
        )

    if (
        resolved_origin_region
        and resolved_destination_region
        and resolved_origin_region != resolved_destination_region
    ):
        lane_factor *= settings.national_cross_region_factor
        notes.append(
            f"Cruce de region {resolved_origin_region}->{resolved_destination_region} con factor {settings.national_cross_region_factor:.2f}."
        )

    origin_zone = _normalize_token(origin_zone_code)
    destination_zone = _normalize_token(destination_zone_code)
    if origin_zone and destination_zone and origin_zone != destination_zone:
        lane_factor *= settings.national_cross_zone_factor
        notes.append(
            f"Cruce de zona operativa {origin_zone}->{destination_zone} con factor {settings.national_cross_zone_factor:.2f}."
        )

    if use_station_handoff:
        lane_factor *= settings.national_station_handoff_factor
        notes.append(
            f"Transferencia entre estaciones de servicio con factor {settings.national_station_handoff_factor:.2f}."
        )

    return NationalLaneDecision(
        origin_state_code=origin_state,
        destination_state_code=destination_state,
        origin_region_code=resolved_origin_region,
        destination_region_code=resolved_destination_region,
        lane_factor=lane_factor,
        notes=notes,
    )

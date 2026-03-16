from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.models import QuotePolicyRule, ZoneSurchargeRule

DEFAULT_SERVICE_FACTORS = {
    "programado": 1.0,
    "express": 1.3,
    "recurrente": 0.9,
    "mandaditos": 1.12,
    "paqueteria": 1.2,
}

DEFAULT_ZONE_FACTORS = {
    "urbana": 1.0,
    "metropolitana": 1.18,
    "intermunicipal": 1.35,
    "rural": 1.45,
}

DEFAULT_RURAL_COMPLEXITY_FACTORS = {
    "baja": 1.04,
    "media": 1.12,
    "alta": 1.25,
}

ALLOWED_ZONE_TYPES = set(DEFAULT_ZONE_FACTORS.keys())
ALLOWED_RURAL_COMPLEXITY = set(DEFAULT_RURAL_COMPLEXITY_FACTORS.keys())

SERVICE_ALIASES = {
    "programada": "programado",
    "programado": "programado",
    "messaging": "programado",
    "package": "paqueteria",
    "paquete": "paqueteria",
    "errand": "mandaditos",
}


@dataclass
class QuotePolicyDecision:
    requested_service_type: str
    applied_service_type: str
    service_converted: bool
    max_distance_km: float | None
    service_factor: float
    zone_factor: float
    complexity_factor: float
    eta_extra_minutes: int
    zone_type: str
    rural_complexity: str
    policy_notes: list[str] = field(default_factory=list)


def normalize_service_type(service_type: str) -> str:
    normalized = (service_type or "").strip().lower()
    if not normalized:
        return "programado"
    return SERVICE_ALIASES.get(normalized, normalized)


def normalize_zone_type(zone_type: str) -> str:
    normalized = (zone_type or "").strip().lower()
    if normalized not in ALLOWED_ZONE_TYPES:
        return "urbana"
    return normalized


def normalize_rural_complexity(rural_complexity: str) -> str:
    normalized = (rural_complexity or "").strip().lower()
    if normalized not in ALLOWED_RURAL_COMPLEXITY:
        return "media"
    return normalized


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _active_validity_filter(model: type[QuotePolicyRule] | type[ZoneSurchargeRule]) -> list[object]:
    now = _now_utc()
    return [
        model.active.is_(True),
        model.valid_from <= now,
        or_(model.valid_to.is_(None), model.valid_to >= now),
    ]


def _get_service_rule(db: Session, service_type: str) -> QuotePolicyRule | None:
    normalized = normalize_service_type(service_type)
    return (
        db.query(QuotePolicyRule)
        .filter(
            QuotePolicyRule.service_type == normalized,
            *_active_validity_filter(QuotePolicyRule),
        )
        .order_by(QuotePolicyRule.valid_from.desc())
        .first()
    )


def _get_zone_rule(db: Session, zone_type: str, rural_complexity: str) -> ZoneSurchargeRule | None:
    normalized_zone = normalize_zone_type(zone_type)
    normalized_complexity = normalize_rural_complexity(rural_complexity)

    if normalized_zone == "rural":
        specific = (
            db.query(ZoneSurchargeRule)
            .filter(
                ZoneSurchargeRule.zone_type == normalized_zone,
                ZoneSurchargeRule.rural_complexity == normalized_complexity,
                *_active_validity_filter(ZoneSurchargeRule),
            )
            .order_by(ZoneSurchargeRule.valid_from.desc())
            .first()
        )
        if specific:
            return specific

    return (
        db.query(ZoneSurchargeRule)
        .filter(
            ZoneSurchargeRule.zone_type == normalized_zone,
            ZoneSurchargeRule.rural_complexity.is_(None),
            *_active_validity_filter(ZoneSurchargeRule),
        )
        .order_by(ZoneSurchargeRule.valid_from.desc())
        .first()
    )


def resolve_quote_policy(
    db: Session,
    requested_service_type: str,
    distance_km: float,
    zone_type: str,
    rural_complexity: str,
) -> QuotePolicyDecision:
    normalized_service = normalize_service_type(requested_service_type)
    normalized_zone = normalize_zone_type(zone_type)
    normalized_complexity = normalize_rural_complexity(rural_complexity)

    service_rule = _get_service_rule(db, normalized_service)
    zone_rule = _get_zone_rule(db, normalized_zone, normalized_complexity)

    applied_service = normalized_service
    service_converted = False
    policy_notes: list[str] = []

    service_factor = DEFAULT_SERVICE_FACTORS.get(normalized_service, 1.0)
    max_distance_km = None

    if service_rule:
        service_factor = float(service_rule.service_factor)
        max_distance_km = service_rule.max_distance_km

    if max_distance_km and distance_km > max_distance_km and service_rule and service_rule.fallback_service_type:
        applied_service = normalize_service_type(service_rule.fallback_service_type)
        service_converted = applied_service != normalized_service
        fallback_rule = _get_service_rule(db, applied_service)
        if fallback_rule:
            service_factor = float(fallback_rule.service_factor)
        else:
            service_factor = DEFAULT_SERVICE_FACTORS.get(applied_service, service_factor)
        if service_converted:
            policy_notes.append(
                f"{normalized_service} solo aplica hasta {max_distance_km:g} km; se convirtio automaticamente a {applied_service}."
            )

    zone_factor = DEFAULT_ZONE_FACTORS.get(normalized_zone, 1.0)
    complexity_factor = 1.0
    eta_extra_minutes = 0

    if zone_rule:
        zone_factor = float(zone_rule.zone_factor)
        complexity_factor = float(zone_rule.complexity_factor)
        eta_extra_minutes = int(zone_rule.eta_extra_minutes)
    elif normalized_zone == "rural":
        complexity_factor = DEFAULT_RURAL_COMPLEXITY_FACTORS[normalized_complexity]
        eta_extra_minutes = 28
    elif normalized_zone == "intermunicipal":
        eta_extra_minutes = 18

    if normalized_zone in {"rural", "intermunicipal"}:
        policy_notes.append(
            "Las zonas rurales o intermunicipales tienen recargos por condiciones operativas y complejidad de cobertura."
        )

    return QuotePolicyDecision(
        requested_service_type=normalized_service,
        applied_service_type=applied_service,
        service_converted=service_converted,
        max_distance_km=max_distance_km,
        service_factor=service_factor,
        zone_factor=zone_factor,
        complexity_factor=complexity_factor,
        eta_extra_minutes=eta_extra_minutes,
        zone_type=normalized_zone,
        rural_complexity=normalized_complexity,
        policy_notes=policy_notes,
    )

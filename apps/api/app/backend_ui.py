from datetime import datetime, timedelta, timezone
from html import escape
import csv
import io
from urllib.parse import quote_plus, urlencode
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.models import (
    ClientKind,
    ClientProfile,
    ContactLead,
    Delivery,
    GeoColony,
    GeoCatalogSync,
    GeoMunicipality,
    GeoPostalCode,
    GeoState,
    Guide,
    GuideParty,
    PricingRule,
    Rider,
    RiderCommission,
    Service,
    ServiceType,
    Station,
    StationCommission,
    User,
    UserRole,
    WorkflowStage,
    Zone,
    ZoneGeoRule,
)
from app.db.sepomex_sync import sync_sepomex_catalog
from app.core.security import hash_password
from app.db.session import get_db
from app.services.commissions import close_rider_week, close_station_week, resolve_week_window

router = APIRouter(prefix="/ERPMande24", tags=["backend-ui"])
legacy_router = APIRouter(prefix="/backend", include_in_schema=False)

MENU = [
    ("dashboard", "Dashboard", "/ERPMande24"),
    ("guides_new", "Generar Guia", "/ERPMande24/guides/new"),
    ("guides", "Guias", "/ERPMande24/guides"),
    ("deliveries", "Entregas", "/ERPMande24/deliveries"),
    ("services", "Servicios", "/ERPMande24/catalogs/services"),
    ("zones", "Zonas", "/ERPMande24/catalogs/zones"),
    ("stations", "Estaciones", "/ERPMande24/catalogs/stations"),
    ("riders", "Riders", "/ERPMande24/catalogs/riders"),
    ("clients", "Clientes", "/ERPMande24/catalogs/clients"),
    ("leads", "Leads Contacto", "/ERPMande24/leads"),
    ("pricing", "Tarifas", "/ERPMande24/catalogs/pricing-rules"),
    ("users", "Usuarios", "/ERPMande24/users"),
    ("comm_rider", "Comisiones Rider", "/ERPMande24/commissions/riders"),
    ("comm_station", "Comisiones Estacion", "/ERPMande24/commissions/stations"),
]

ROLE_OPTIONS = ["admin", "station", "rider", "client"]

MODULE_ICON_SVG = {
    "dashboard": "<rect x='3' y='3' width='18' height='18' rx='4'/><path d='M7.5 15.5v-3.5M12 15.5V8.5M16.5 15.5v-5.5'/>",
    "guides_new": "<path d='M7 4h7l4 4v12H7z'/><path d='M14 4v4h4'/><path d='M12 11v6M9 14h6'/>",
    "guides": "<path d='M7 4h7l4 4v12H7z'/><path d='M14 4v4h4'/><path d='M9 12h6M9 15h6'/>",
    "deliveries": "<path d='M3 9h11v7H3z'/><path d='M14 11h3l4 4v1h-7z'/><circle cx='7.5' cy='18' r='1.5'/><circle cx='17.5' cy='18' r='1.5'/>",
    "services": "<path d='M6 4h12l2 4-8 4-8-4z'/><path d='M4 8v8l8 4 8-4V8'/>",
    "zones": "<path d='M12 21s6-5.8 6-10.1a6 6 0 1 0-12 0C6 15.2 12 21 12 21z'/><circle cx='12' cy='11' r='2.2'/>",
    "stations": "<path d='M4 20h16'/><rect x='6' y='5' width='12' height='15' rx='2'/><path d='M9 9h2M13 9h2M9 13h2M13 13h2'/>",
    "riders": "<circle cx='10' cy='7.5' r='2'/><path d='M10 10v4l3 2.2'/><path d='M8 13.5l-2.5 2.5'/><circle cx='7' cy='18' r='2'/><circle cx='17' cy='18' r='2'/><path d='M12.5 14.2h2.7L18 18'/>",
    "clients": "<circle cx='8.5' cy='9' r='2.3'/><circle cx='15.8' cy='9.8' r='2'/><path d='M4.5 18c.9-2 2.4-3.1 4-3.1S11.7 16 12.6 18'/><path d='M12.8 18c.6-1.4 1.7-2.2 3.1-2.2 1.2 0 2.2.5 2.9 1.5'/>",
    "leads": "<path d='M4 6h16v12H4z'/><path d='M4 8l8 5 8-5'/><circle cx='18.2' cy='6' r='2.2'/>",
    "pricing": "<circle cx='12' cy='12' r='8'/><path d='M14.8 9.2c-.6-.7-1.5-1.1-2.7-1.1-1.7 0-2.9.9-2.9 2.2 0 1.3 1 1.9 2.6 2.2l1 .2c.9.2 1.4.5 1.4 1.1 0 .7-.7 1.3-1.9 1.3-1 0-1.9-.4-2.7-1.1'/><path d='M12 7v10'/>",
    "users": "<path d='M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z'/><circle cx='12' cy='10' r='2.1'/><path d='M9.3 14.6c.8-1.1 1.7-1.7 2.7-1.7s1.9.6 2.7 1.7'/>",
    "comm_rider": "<circle cx='12' cy='12' r='8'/><path d='M8.8 10.2h4.5a1.6 1.6 0 1 1 0 3.2h-2.4a1.6 1.6 0 1 0 0 3.2h4.3'/><path d='M11.7 8.6v7.8'/><path d='M16.6 7.4l1.6-1.6'/><path d='M16.6 16.6l1.6 1.6'/>",
    "comm_station": "<path d='M4 20h16'/><path d='M6 20V9l6-4 6 4v11'/><path d='M9 14h6'/><path d='M12 11v6'/>",
    "swagger": "<path d='M8 6c-2 0-3 1.2-3 3v2c0 1.2-.5 1.8-1.5 2 1 .2 1.5.8 1.5 2v2c0 1.8 1 3 3 3'/><path d='M16 6c2 0 3 1.2 3 3v2c0 1.2.5 1.8 1.5 2-1 .2-1.5.8-1.5 2v2c0 1.8-1 3-3 3'/><path d='M11 8h2v8h-2z'/>",
}

MODULE_GROUP = {
    "dashboard": "Monitoreo",
    "guides_new": "Operacion",
    "guides": "Operacion",
    "deliveries": "Operacion",
    "services": "Catalogos",
    "zones": "Catalogos",
    "stations": "Catalogos",
    "riders": "Catalogos",
    "clients": "Clientes",
    "leads": "Clientes",
    "pricing": "Comercial",
    "users": "Seguridad",
    "comm_rider": "Finanzas",
    "comm_station": "Finanzas",
    "swagger": "Integracion",
}

ROLE_MODULES = {
    "admin": {key for key, _label, _href in MENU},
    "station": {"guides_new", "guides", "deliveries", "comm_rider", "comm_station"},
    "rider": {"guides", "deliveries"},
    "client": {"guides", "deliveries"},
}

ERP_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="Icono ERPMande24">
    <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#ff8a1f"/>
            <stop offset="100%" stop-color="#c2410c"/>
        </linearGradient>
        <linearGradient id="s" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#fff1df"/>
            <stop offset="100%" stop-color="#ffd3ad"/>
        </linearGradient>
    </defs>
    <rect x="8" y="8" width="112" height="112" rx="30" fill="url(#g)"/>
    <rect x="22" y="22" width="84" height="84" rx="22" fill="#ffffff1f"/>
    <path d="M30 80c8-10 20-20 35-30 8 8 18 15 30 20" fill="none" stroke="#fff5eb" stroke-width="7" stroke-linecap="round"/>
    <rect x="40" y="47" width="48" height="34" rx="9" fill="url(#s)" stroke="#8a2f08" stroke-width="2.2"/>
    <path d="M40 59h48" stroke="#8a2f08" stroke-width="2.2"/>
    <path d="M64 47v34" stroke="#8a2f08" stroke-width="2.2"/>
    <circle cx="44" cy="88" r="7" fill="#ffe6d1"/>
    <circle cx="84" cy="88" r="7" fill="#ffe6d1"/>
    <circle cx="92" cy="36" r="14" fill="#7c2d12"/>
    <text x="92" y="40" text-anchor="middle" font-family="Trebuchet MS, sans-serif" font-size="11" font-weight="800" fill="#fff7ed">24</text>
</svg>"""


@legacy_router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@legacy_router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def backend_legacy_redirect(request: Request, full_path: str = "") -> RedirectResponse:
    target = f"/ERPMande24/{full_path}" if full_path else "/ERPMande24"
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(url=target, status_code=307)


@router.get("/icon.svg")
def backend_icon_svg() -> Response:
    return Response(content=ERP_ICON_SVG, media_type="image/svg+xml")


def _base_css() -> str:
    return """
:root {
        --bg: #fff7ed;
  --surface: #ffffff;
        --surface-2: #ffedd5;
        --sidebar: #9a3412;
        --sidebar-line: #c2410c;
    --ink: #17293f;
    --ink-soft: #58708e;
        --line: #f0c6a6;
        --brand: #ea580c;
        --brand-2: #c2410c;
  --ok: #166534;
  --warn: #9a3412;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  color: var(--ink);
  font-family: "Avenir Next", "Trebuchet MS", sans-serif;
  background:
        radial-gradient(circle at 0% 0%, #fff7ed 0%, transparent 30%),
        radial-gradient(circle at 100% 0%, #fed7aa 0%, transparent 28%),
    var(--bg);
}

.layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 270px 1fr;
}

.sidebar {
    background: linear-gradient(170deg, #7c2d12 0%, var(--sidebar) 70%, #c2410c 100%);
  color: #dbe7ff;
  padding: 1rem;
  border-right: 1px solid var(--sidebar-line);
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.brand-logo {
    width: 32px;
    height: 32px;
    border-radius: 10px;
    box-shadow: 0 8px 14px rgba(194, 65, 12, 0.35);
}

.brand-row h2 {
  margin: 0;
  font-size: 1.05rem;
}

.brand-copy {
    display: grid;
    gap: 0.06rem;
}

.brand-copy small {
    color: #fed7aa;
    font-size: 0.72rem;
}

.tag {
  display: inline-block;
  margin-top: 0.5rem;
  font-size: 0.76rem;
  border-radius: 999px;
  padding: 0.16rem 0.52rem;
    background: #7c2d12;
    color: #ffedd5;
}

.menu {
  margin-top: 1rem;
  display: grid;
  gap: 0.42rem;
}

.menu a {
  color: #d6e0ef;
  text-decoration: none;
  border: 1px solid #3b4959;
  border-radius: 8px;
    padding: 0.36rem 0.5rem;
  font-size: 0.9rem;
  background: rgba(17, 24, 39, 0.35);
    display: grid;
    grid-template-columns: 34px 1fr;
    align-items: center;
    gap: 0.45rem;
}

.menu a .mod-ico {
    width: 30px;
    height: 30px;
    padding: 5px;
    box-sizing: border-box;
    border-radius: 8px;
    border: 1px solid #6a7584;
    background: rgba(251, 146, 60, 0.16);
    color: #fff7ed;
    display: block;
}

.menu a .mod-label {
    display: grid;
    gap: 0.08rem;
}

.menu a .mod-label small {
    color: #b9c8dc;
    font-size: 0.68rem;
}

.menu a.active {
        background: linear-gradient(120deg, var(--brand), #fb923c);
  border-color: transparent;
  color: #fff;
}

.menu a.active .mod-ico {
    border-color: #fff3e0;
    background: rgba(255, 255, 255, 0.2);
}

.module-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    gap: 0.65rem;
}

.module-card {
    text-decoration: none;
    color: var(--ink);
    border: 1px solid var(--line);
    border-radius: 12px;
    background: linear-gradient(140deg, #fff, #fff7ed);
    padding: 0.72rem;
    display: grid;
    gap: 0.4rem;
}

.module-card:hover {
    border-color: #ea580c;
}

.module-head {
    display: flex;
    align-items: center;
    gap: 0.45rem;
}

.module-head .mod-ico {
    width: 34px;
    height: 34px;
    padding: 5px;
    box-sizing: border-box;
    border-radius: 9px;
    border: 1px solid #f2b183;
    background: linear-gradient(130deg, #fb923c, #c2410c);
    color: #fff;
    display: block;
}

.module-meta {
    color: #6b7280;
    font-size: 0.74rem;
}

.content {
  padding: 1rem;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.8rem;
  flex-wrap: wrap;
}

h1 {
  margin: 0.2rem 0;
  font-size: clamp(1.45rem, 3vw, 2.05rem);
  line-height: 1.06;
}

.subtitle {
  margin: 0;
  color: var(--ink-soft);
  max-width: 76ch;
}

.top-actions {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.panel {
  margin-top: 1rem;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
  padding: 0.95rem;
}

.panel h3 {
  margin: 0.05rem 0 0.75rem;
}

.hero-shell {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 0.85rem;
    align-items: center;
    background: linear-gradient(132deg, #fff7ed, #ffedd5);
}

.hero-shell p {
    margin: 0.35rem 0;
    color: #43515b;
}

.hero-badge {
    display: inline-block;
    border-radius: 999px;
    font-size: 0.75rem;
    padding: 0.16rem 0.5rem;
    background: #ea580c;
    color: #fff;
}

.hero-media {
    border: 1px solid #f0c6a6;
    border-radius: 12px;
    overflow: hidden;
    background: #fff;
}

.hero-media svg {
    width: 100%;
    display: block;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.62rem;
}

.kpi {
  border: 1px solid #cdd8de;
  border-radius: 10px;
        background: linear-gradient(180deg, #fff7ed, #ffffff);
  padding: 0.55rem;
}

.kpi small {
  color: #4f5f67;
  display: block;
}

.kpi strong {
  display: block;
  margin-top: 0.2rem;
  font-size: 1.08rem;
}

.trend-up {
    color: var(--ok);
}

.trend-down {
    color: var(--warn);
}

.trend-neutral {
    color: #475569;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 0.72rem;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 0.72rem;
}

label {
  display: grid;
  gap: 0.35rem;
  font-weight: 600;
}

input,
select,
textarea {
  border: 1px solid var(--line);
  border-radius: 9px;
  padding: 0.52rem 0.62rem;
  background: #fff;
  color: var(--ink);
}

textarea {
  min-height: 80px;
}

.full {
  grid-column: 1 / -1;
}

.actions {
  margin-top: 0.35rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

button,
.btn {
  cursor: pointer;
  border: 1px solid var(--line);
  border-radius: 9px;
  padding: 0.5rem 0.84rem;
  background: #fff;
  color: var(--ink);
  text-decoration: none;
  display: inline-block;
}

button.primary,
.btn.primary {
  border-color: transparent;
  color: #fff;
  background: linear-gradient(120deg, var(--brand), var(--brand-2));
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 640px;
}

th,
td {
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
  padding: 0.52rem;
  font-size: 0.9rem;
  vertical-align: top;
}

th {
  background: var(--surface-2);
}

.table-wrap {
  overflow-x: auto;
}

.msg {
  margin-top: 0.55rem;
  font-weight: 700;
  color: var(--ok);
}

.msg.error {
  color: var(--warn);
}

.inline-form {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.badge {
  border: 1px solid #cadce1;
  border-radius: 999px;
  padding: 0.1rem 0.48rem;
  background: #f0f9ff;
  font-size: 0.78rem;
}

.tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-bottom: 0.6rem;
}

.tabs a {
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 0.24rem 0.65rem;
    text-decoration: none;
    color: var(--ink);
    font-size: 0.86rem;
    background: #fff;
}

.empty {
  padding: 0.65rem;
  border: 1px dashed #d1c7b8;
  border-radius: 10px;
  background: #fffaf2;
  color: #5f4d34;
}

@media (max-width: 1040px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { border-right: 0; border-bottom: 1px solid var(--sidebar-line); }
}

@media (max-width: 760px) {
  .grid, .grid-3 { grid-template-columns: 1fr; }
    .hero-shell { grid-template-columns: 1fr; }
}
"""


def _module_icon_svg(key: str, css_class: str = "mod-ico") -> str:
    body = MODULE_ICON_SVG.get(key, MODULE_ICON_SVG["dashboard"])
    return (
        f'<svg class="{css_class}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )


def _modules_for_role(role: str) -> list[tuple[str, str, str]]:
    allowed = ROLE_MODULES.get(role, set())
    return [item for item in MENU if item[0] in allowed]


def _menu_html(active: str, role: str) -> str:
    rows: list[str] = []
    for key, label, href in _modules_for_role(role):
        cls = "active" if key == active else ""
        group = MODULE_GROUP.get(key, "Modulo")
        rows.append(
            f'<a href="{href}" class="{cls}">{_module_icon_svg(key)}<span class="mod-label">{label}<small>{group}</small></span></a>'
        )
    if role == "admin":
        rows.append(f'<a href="/docs">{_module_icon_svg("swagger")}<span class="mod-label">Swagger API<small>Integracion</small></span></a>')
    return "".join(rows)


def _role_from_request(request: Request) -> str:
    role_cookie = request.cookies.get("m24_erpmande24_role") or request.cookies.get("m24_backend_role") or "admin"
    role = role_cookie.strip().lower()
    return role if role in ROLE_OPTIONS else "admin"


def _role_switcher(current_role: str, return_to: str) -> str:
    options = "".join(
        [
            f'<option value="{item}" {"selected" if item == current_role else ""}>{item}</option>'
            for item in ROLE_OPTIONS
        ]
    )
    return (
        '<section style="margin-top:0.8rem;padding-top:0.8rem;border-top:1px solid #3b4959;">'
        '<small style="color:#ffedd5;display:block;margin-bottom:0.3rem;">Rol ERPMande24</small>'
        '<form method="post" action="/ERPMande24/role/select" style="display:grid;gap:0.35rem;">'
        f'<input type="hidden" name="return_to" value="{escape(return_to)}" />'
        f'<select name="role">{options}</select>'
        '<button type="submit">Aplicar Rol</button>'
        '</form></section>'
    )


def _can_manage(role: str) -> bool:
    return role == "admin"


def _can_ops(role: str) -> bool:
    return role in {"admin", "station"}


def _check_role_or_redirect(role: str, allowed: set[str], redirect_to: str, action_label: str) -> RedirectResponse | None:
    if role not in allowed:
        return _redirect(redirect_to, f"Sin permisos para {action_label} con rol {role}.", "error")
    return None


def _pagination(path: str, page: int, page_size: int, total: int, query_params: dict[str, str] | None = None) -> str:
    if total <= page_size:
        return ""
    total_pages = max(1, (total + page_size - 1) // page_size)
    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)

    base_params = dict(query_params or {})

    def _build_link(target_page: int) -> str:
        params = {**base_params, "page": str(target_page), "page_size": str(page_size)}
        return f"{path}?{urlencode(params)}"

    return (
        '<div class="actions">'
        f'<span class="badge">Pagina {page} de {total_pages}</span>'
        f'<a class="btn" href="{_build_link(1)}">Primera</a>'
        f'<a class="btn" href="{_build_link(prev_page)}">Anterior</a>'
        f'<a class="btn" href="{_build_link(next_page)}">Siguiente</a>'
        f'<a class="btn" href="{_build_link(total_pages)}">Ultima</a>'
        '</div>'
    )


def _timeline(events: list[tuple[str, str]]) -> str:
    if not events:
        return '<div class="empty">Sin eventos disponibles.</div>'
    lines = []
    for when, text in events:
        lines.append(
            "<div style=\"display:grid;grid-template-columns:150px 1fr;gap:0.5rem;padding:0.35rem 0;border-bottom:1px dashed #d8dde4;\">"
            f"<small>{escape(when)}</small><div>{escape(text)}</div></div>"
        )
    return "".join(lines)


def _render_layout(
    active: str,
    title: str,
    subtitle: str,
    content: str,
    msg: str = "",
    kind: str = "ok",
    request: Request | None = None,
    current_role: str | None = None,
    current_path: str | None = None,
) -> str:
    role_value = current_role or (_role_from_request(request) if request else "admin")
    path_value = current_path or (str(request.url.path) if request else "/ERPMande24")

    msg_html = ""
    if msg:
        css = "msg error" if kind == "error" else "msg"
        msg_html = f'<p class="{css}">{escape(msg)}</p>'

    script = (
        "<script>"
        "document.addEventListener('submit', function (ev) {"
        "  var form = ev.target;"
        "  var message = form.getAttribute('data-confirm');"
        "  if (message && !window.confirm(message)) { ev.preventDefault(); }"
        "});"
        "</script>"
    )

    hero_block = (
        '<section class="panel hero-shell">'
        '<div>'
        '<span class="hero-badge">ERPMande24</span>'
        '<h3>Operacion mas clara con identidad visual unificada</h3>'
        '<p>Administra guias, entregas, comisiones y catalogos en una interfaz mas amigable para el equipo operativo.</p>'
        '<p><strong>Servicios:</strong> Mensajeria | Paqueteria | Mandaditos</p>'
        '</div>'
        '<div class="hero-media">'
        '<svg viewBox="0 0 600 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Banner ERPMande24">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#ff8a1f"/><stop offset="100%" stop-color="#c2410c"/></linearGradient><linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fff1df"/><stop offset="100%" stop-color="#ffd3ad"/></linearGradient></defs>'
        '<rect width="600" height="280" fill="url(#g)"/>'
        '<circle cx="76" cy="46" r="64" fill="#ffffff15"/>'
        '<circle cx="568" cy="268" r="96" fill="#ffffff10"/>'
        '<rect x="28" y="62" width="330" height="192" rx="18" fill="#ffffff18" stroke="#ffffff2a"/>'
        '<text x="50" y="124" font-family="Trebuchet MS, sans-serif" font-size="40" font-weight="700" fill="#fffaf5">Mande24</text>'
        '<rect x="50" y="136" width="248" height="3" rx="2" fill="#ffd3ad"/>'
        '<text x="50" y="164" font-family="Trebuchet MS, sans-serif" font-size="16" font-weight="700" fill="#fff1df">Mensajeria | Paqueteria | Mandaditos</text>'
        '<text x="50" y="188" font-family="Trebuchet MS, sans-serif" font-size="13" fill="#fffaf5">Entrega local rapida con seguimiento claro.</text>'
        '<rect x="50" y="203" width="252" height="30" rx="15" fill="#fff1df"/>'
        '<text x="66" y="223" font-family="Trebuchet MS, sans-serif" font-size="13" font-weight="700" fill="#8a2f08">ERPMande24: control operativo y comercial.</text>'
        '<rect x="374" y="36" width="204" height="206" rx="20" fill="#ffffff1a" stroke="#ffffff30"/>'
        '<rect x="406" y="62" width="140" height="152" rx="28" fill="#ffffff20"/>'
        '<path d="M400 184c12-14 30-28 52-42 10 9 23 17 39 24" fill="none" stroke="#fff5eb" stroke-width="8" stroke-linecap="round"/>'
        '<rect x="438" y="122" width="76" height="56" rx="11" fill="url(#b)" stroke="#8a2f08" stroke-width="3"/>'
        '<path d="M438 140h76" stroke="#8a2f08" stroke-width="3"/>'
        '<path d="M476 122v56" stroke="#8a2f08" stroke-width="3"/>'
        '<circle cx="446" cy="188" r="8" fill="#ffe6d1"/>'
        '<circle cx="506" cy="188" r="8" fill="#ffe6d1"/>'
        '<circle cx="530" cy="102" r="18" fill="#7c2d12"/>'
        '<text x="530" y="108" text-anchor="middle" font-family="Trebuchet MS, sans-serif" font-size="13" font-weight="700" fill="#fff7ed">24</text>'
        '</svg>'
        '</div>'
        '</section>'
    )

    return (
        "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\" />"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />"
        "<link rel=\"icon\" type=\"image/svg+xml\" href=\"/ERPMande24/icon.svg?v=2\" />"
        f"<title>ERPMande24 | {escape(title)}</title>"
        f"<style>{_base_css()}</style></head><body>"
        "<div class=\"layout\">"
        "<aside class=\"sidebar\">"
        "<div class=\"brand-row\"><img class=\"brand-logo\" src=\"/ERPMande24/icon.svg?v=2\" alt=\"Icono ERPMande24\" /><div class=\"brand-copy\"><h2>ERPMande24</h2><small>Entrega segura. Ruta inteligente.</small></div></div>"
        "<span class=\"tag\">ERPMande24 Admin</span>"
        f"<nav class=\"menu\">{_menu_html(active, role_value)}</nav>{_role_switcher(role_value, path_value)}</aside>"
        "<main class=\"content\">"
        f"<header class=\"header\"><div><h1>{escape(title)}</h1><p class=\"subtitle\">{escape(subtitle)}</p></div>"
        "<div class=\"top-actions\"><a class=\"btn\" href=\"/ERPMande24\">Dashboard</a><a class=\"btn primary\" href=\"/ERPMande24/guides/new\">Nueva Guia</a></div></header>"
        f"{hero_block}{msg_html}{content}</main></div>{script}</body></html>"
    )


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return '<div class="empty">Sin registros para mostrar.</div>'
    head = "".join([f"<th>{escape(item)}</th>" for item in headers])
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join([f"<td>{item}</td>" for item in row]) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def _redirect(url: str, msg: str, kind: str = "ok") -> RedirectResponse:
    sep = "&" if "?" in url else "?"
    target = f"{url}{sep}msg={quote_plus(msg)}&kind={quote_plus(kind)}"
    return RedirectResponse(url=target, status_code=303)


def _querybox(action: str, placeholder: str, q_value: str = "") -> str:
    return (
        f'<form class="actions" method="get" action="{action}">'
        f'<input name="q" value="{escape(q_value)}" placeholder="{escape(placeholder)}" />'
        '<button type="submit">Buscar</button>'
        f'<a class="btn" href="{action}">Limpiar</a>'
        '</form>'
    )


def _bar_chart(title: str, points: list[tuple[str, int]]) -> str:
    if not points:
        return f'<section class="panel"><h3>{escape(title)}</h3><div class="empty">Sin datos.</div></section>'

    max_value = max(value for _, value in points) or 1
    bars: list[str] = []
    for label, value in points:
        width = max(2, int((value / max_value) * 100))
        bars.append(
            "<div style=\"display:grid;grid-template-columns:130px 1fr 50px;gap:0.5rem;align-items:center;margin:0.35rem 0;\">"
            f"<small>{escape(label)}</small>"
            f"<div style=\"height:12px;border-radius:99px;background:#f4ddd0;overflow:hidden;\"><div style=\"height:100%;width:{width}%;background:linear-gradient(120deg,#ea580c,#fb923c);\"></div></div>"
            f"<strong style=\"font-size:0.86rem;\">{value}</strong>"
            "</div>"
        )

    return f'<section class="panel"><h3>{escape(title)}</h3>{"".join(bars)}</section>'


def _bulk_form(form_id: str, action: str, label: str) -> str:
    return (
        f'<form id="{form_id}" class="actions" method="post" action="{action}" data-confirm="Esta accion cambiara multiples registros. Deseas continuar?">'
        '<select name="active">'
        '<option value="true">Activar seleccionados</option>'
        '<option value="false">Desactivar seleccionados</option>'
        '</select>'
        f'<button type="submit">{escape(label)}</button>'
        '</form>'
    )


def _tabs(items: list[tuple[str, str]]) -> str:
    links = "".join([f'<a href="#{escape(anchor)}">{escape(label)}</a>' for anchor, label in items])
    return f'<div class="tabs">{links}</div>'


def _csv_response(filename: str, headers: list[str], rows: list[list[str]]) -> Response:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    content = buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _require_manage(request: Request, redirect_to: str, action_label: str) -> RedirectResponse | None:
    role = _role_from_request(request)
    return _check_role_or_redirect(role, {"admin"}, redirect_to, action_label)


def _require_ops(request: Request, redirect_to: str, action_label: str) -> RedirectResponse | None:
    role = _role_from_request(request)
    return _check_role_or_redirect(role, {"admin", "station"}, redirect_to, action_label)


@router.post("/role/select")
def backend_select_role(role: str = Form("admin"), return_to: str = Form("/ERPMande24")) -> RedirectResponse:
    selected = role if role in ROLE_OPTIONS else "admin"
    response = RedirectResponse(url=return_to or "/ERPMande24", status_code=303)
    response.set_cookie("m24_erpmande24_role", selected, httponly=False, samesite="lax")
    return response


def _seed_demo_data(db: Session) -> dict[str, str]:
    zone = db.query(Zone).filter(Zone.code == "ZN-DEMO").first()
    if not zone:
        zone = Zone(name="Zona Demo", code="ZN-DEMO", active=True)
        db.add(zone)
        db.flush()

    station = db.query(Station).filter(Station.name == "Estacion Demo").first()
    if not station:
        station = Station(name="Estacion Demo", zone_id=zone.id, active=True)
        db.add(station)
        db.flush()

    service = db.query(Service).filter(Service.name == "Servicio Demo").first()
    if not service:
        service = Service(
            name="Servicio Demo",
            description="Servicio base demo",
            service_type=ServiceType.messaging,
            active=True,
        )
        db.add(service)
        db.flush()

    rule = (
        db.query(PricingRule)
        .filter(PricingRule.service_id == service.id, PricingRule.station_id == station.id)
        .first()
    )
    if not rule:
        db.add(PricingRule(service_id=service.id, station_id=station.id, price=120.0, currency="MXN", active=True))

    db.commit()
    return {"zone_id": zone.id, "station_id": station.id, "service_id": service.id}


@router.get("", response_class=HTMLResponse)
def backend_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    msg: str = "",
    kind: str = "ok",
    period: str = "7d",
) -> str:
    today = datetime.now(timezone.utc).date()
    now_dt = datetime.now(timezone.utc)

    allowed_periods = {"today", "7d", "30d", "all"}
    safe_period = period if period in allowed_periods else "7d"
    lead_filters = []
    previous_filters = []
    period_label = "Ultimos 7 dias"
    previous_label = "Periodo anterior"
    if safe_period == "today":
        lead_filters.append(func.date(ContactLead.created_at) == today)
        previous_filters.append(func.date(ContactLead.created_at) == (today - timedelta(days=1)))
        period_label = "Hoy"
        previous_label = "Ayer"
    elif safe_period == "7d":
        current_start = now_dt - timedelta(days=7)
        previous_start = now_dt - timedelta(days=14)
        previous_end = current_start
        lead_filters.append(ContactLead.created_at >= current_start)
        previous_filters.extend([ContactLead.created_at >= previous_start, ContactLead.created_at < previous_end])
        period_label = "Ultimos 7 dias"
        previous_label = "7 dias previos"
    elif safe_period == "30d":
        current_start = now_dt - timedelta(days=30)
        previous_start = now_dt - timedelta(days=60)
        previous_end = current_start
        lead_filters.append(ContactLead.created_at >= current_start)
        previous_filters.extend([ContactLead.created_at >= previous_start, ContactLead.created_at < previous_end])
        period_label = "Ultimos 30 dias"
        previous_label = "30 dias previos"
    else:
        period_label = "Historico completo"
        previous_label = "No aplica"

    guides_total = db.query(func.count(Guide.id)).scalar() or 0
    deliveries_total = db.query(func.count(Delivery.id)).scalar() or 0
    delivered_total = db.query(func.count(Delivery.id)).filter(Delivery.stage == WorkflowStage.delivered).scalar() or 0
    services_total = db.query(func.count(Service.id)).scalar() or 0
    stations_total = db.query(func.count(Station.id)).scalar() or 0
    riders_total = db.query(func.count(Rider.id)).scalar() or 0
    leads_total = db.query(func.count(ContactLead.id)).filter(*lead_filters).scalar() or 0
    leads_new = db.query(func.count(ContactLead.id)).filter(*lead_filters, ContactLead.status == "new").scalar() or 0
    leads_contacted = db.query(func.count(ContactLead.id)).filter(*lead_filters, ContactLead.status == "contacted").scalar() or 0
    leads_closed = db.query(func.count(ContactLead.id)).filter(*lead_filters, ContactLead.status == "closed").scalar() or 0

    leads_prev_total = 0
    leads_prev_contacted = 0
    leads_prev_closed = 0
    if previous_filters:
        leads_prev_total = db.query(func.count(ContactLead.id)).filter(*previous_filters).scalar() or 0
        leads_prev_contacted = db.query(func.count(ContactLead.id)).filter(*previous_filters, ContactLead.status == "contacted").scalar() or 0
        leads_prev_closed = db.query(func.count(ContactLead.id)).filter(*previous_filters, ContactLead.status == "closed").scalar() or 0
    sepomex_sync = db.query(GeoCatalogSync).filter(GeoCatalogSync.key == "sepomex_last_sync").first()
    sepomex_catalog_date = db.query(GeoCatalogSync).filter(GeoCatalogSync.key == "sepomex_catalog_date").first()

    guides_today = db.query(func.count(Guide.id)).filter(func.date(Guide.created_at) == today).scalar() or 0
    deliveries_today = db.query(func.count(Delivery.id)).filter(func.date(Delivery.created_at) == today).scalar() or 0
    leads_today = db.query(func.count(ContactLead.id)).filter(func.date(ContactLead.created_at) == today).scalar() or 0

    conversion_pct = 0.0
    if leads_total:
        conversion_pct = ((leads_contacted + leads_closed) / leads_total) * 100

    previous_conversion_pct = 0.0
    if leads_prev_total:
        previous_conversion_pct = ((leads_prev_contacted + leads_prev_closed) / leads_prev_total) * 100

    leads_delta_label = "N/A"
    conversion_delta_label = "N/A"
    leads_delta_css = "trend-neutral"
    conversion_delta_css = "trend-neutral"
    leads_delta_prefix = "FLAT "
    conversion_delta_prefix = "FLAT "
    if previous_filters:
        if leads_prev_total:
            leads_delta = ((leads_total - leads_prev_total) / leads_prev_total) * 100
            leads_delta_label = f"{leads_delta:+.1f}% vs {previous_label}"
            leads_delta_css = "trend-up" if leads_delta > 0 else ("trend-down" if leads_delta < 0 else "trend-neutral")
            leads_delta_prefix = "UP " if leads_delta > 0 else ("DOWN " if leads_delta < 0 else "FLAT ")
        else:
            leads_delta_label = "+100.0% vs periodo sin leads" if leads_total else "0.0% vs periodo sin leads"
            leads_delta_css = "trend-up" if leads_total else "trend-neutral"
            leads_delta_prefix = "UP " if leads_total else "FLAT "

        conversion_delta = conversion_pct - previous_conversion_pct
        conversion_delta_label = f"{conversion_delta:+.1f} pp vs {previous_label}"
        conversion_delta_css = "trend-up" if conversion_delta > 0 else ("trend-down" if conversion_delta < 0 else "trend-neutral")
        conversion_delta_prefix = "UP " if conversion_delta > 0 else ("DOWN " if conversion_delta < 0 else "FLAT ")

    stage_rows = (
        db.query(Delivery.stage, func.count(Delivery.id))
        .group_by(Delivery.stage)
        .order_by(func.count(Delivery.id).desc())
        .all()
    )

    seven_days = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        count = db.query(func.count(Guide.id)).filter(func.date(Guide.created_at) == day).scalar() or 0
        seven_days.append((day.strftime("%m-%d"), int(count)))

    latest_guides = db.query(Guide).order_by(Guide.created_at.desc()).limit(10).all()

    stage_table = _table(
        ["Etapa", "Cantidad"],
        [[escape(item[0].value), str(item[1])] for item in stage_rows],
    )
    stage_chart = _bar_chart("Entregas Por Etapa", [(item[0].value, int(item[1])) for item in stage_rows])
    guides_7d_chart = _bar_chart("Guias Ultimos 7 Dias", seven_days)
    leads_chart = _bar_chart(
        f"Embudo de Leads ({period_label})",
        [
            ("new", int(leads_new)),
            ("contacted", int(leads_contacted)),
            ("closed", int(leads_closed)),
        ],
    )

    lead_period_form = (
        '<form class="actions" method="get" action="/ERPMande24">'
        '<label>Periodo Leads<select name="period">'
        f'<option value="today" {"selected" if safe_period == "today" else ""}>Hoy</option>'
        f'<option value="7d" {"selected" if safe_period == "7d" else ""}>Ultimos 7 dias</option>'
        f'<option value="30d" {"selected" if safe_period == "30d" else ""}>Ultimos 30 dias</option>'
        f'<option value="all" {"selected" if safe_period == "all" else ""}>Todo</option>'
        '</select></label>'
        '<button type="submit">Aplicar</button>'
        '</form>'
    )

    guide_table = _table(
        ["Guia", "Cliente", "Destino", "Monto", "Fecha"],
        [
            [
                f'<a href="/ERPMande24/guides">{escape(item.guide_code)}</a>',
                escape(item.customer_name),
                escape(item.destination_name),
                f"{item.sale_amount:.2f} {escape(item.currency)}",
                item.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for item in latest_guides
        ],
    )

    module_cards = []
    for key, label, href in _modules_for_role(role_value):
        group = MODULE_GROUP.get(key, "Modulo")
        module_cards.append(
            f'<a class="module-card" href="{href}"><div class="module-head">{_module_icon_svg(key)}<strong>{label}</strong></div><small class="module-meta">Grupo: {group}</small></a>'
        )

    content = (
        f"<section class=\"panel\"><h3>Modulos ERPMande24</h3><div class=\"module-grid\">{''.join(module_cards)}</div></section>"
        "<section class=\"panel\"><h3>Indicadores Principales</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>Guias Totales</small><strong>{guides_total}</strong></article>"
        f"<article class=\"kpi\"><small>Entregas Totales</small><strong>{deliveries_total}</strong></article>"
        f"<article class=\"kpi\"><small>Entregadas</small><strong>{delivered_total}</strong></article>"
        f"<article class=\"kpi\"><small>Guias Hoy</small><strong>{guides_today}</strong></article>"
        f"<article class=\"kpi\"><small>Entregas Hoy</small><strong>{deliveries_today}</strong></article>"
        f"<article class=\"kpi\"><small>Servicios</small><strong>{services_total}</strong></article>"
        f"<article class=\"kpi\"><small>Estaciones</small><strong>{stations_total}</strong></article>"
        f"<article class=\"kpi\"><small>Riders</small><strong>{riders_total}</strong></article>"
        "</div></section>"
        "<section class=\"panel\"><h3>Leads Comerciales</h3>"
        f"{lead_period_form}"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>Total Leads ({period_label})</small><strong>{leads_total}</strong></article>"
        f"<article class=\"kpi\"><small>Leads Hoy</small><strong>{leads_today}</strong></article>"
        f"<article class=\"kpi\"><small>new</small><strong>{leads_new}</strong></article>"
        f"<article class=\"kpi\"><small>contacted</small><strong>{leads_contacted}</strong></article>"
        f"<article class=\"kpi\"><small>closed</small><strong>{leads_closed}</strong></article>"
        f"<article class=\"kpi\"><small>Conversion</small><strong>{conversion_pct:.1f}%</strong></article>"
        f"<article class=\"kpi\"><small>Variacion Leads</small><strong class=\"{leads_delta_css}\">{escape(leads_delta_prefix + leads_delta_label)}</strong></article>"
        f"<article class=\"kpi\"><small>Variacion Conversion</small><strong class=\"{conversion_delta_css}\">{escape(conversion_delta_prefix + conversion_delta_label)}</strong></article>"
        "</div>"
        "<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/leads\">Abrir Leads</a><a class=\"btn\" href=\"/ERPMande24/export/leads.csv\">Exportar Leads CSV</a></div>"
        "</section>"
        "<section class=\"panel\"><h3>SEPOMEX</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>Ultima Sync</small><strong>{escape(sepomex_sync.value if sepomex_sync else 'Sin registro')}</strong></article>"
        f"<article class=\"kpi\"><small>Fecha Catalogo</small><strong>{escape(sepomex_catalog_date.value if sepomex_catalog_date else 'No detectada')}</strong></article>"
        f"<article class=\"kpi\"><small>Colonias</small><strong>{db.query(func.count(GeoColony.id)).scalar() or 0}</strong></article>"
        "</div>"
        "<form class=\"actions\" method=\"post\" action=\"/ERPMande24/geo/sync-sepomex\">"
        "<button class=\"primary\" type=\"submit\">Forzar sync SEPOMEX ahora</button>"
        "</form></section>"
        f"<section class=\"panel\"><h3>Distribucion por Etapa</h3>{stage_table}</section>"
        f"{stage_chart}"
        f"{guides_7d_chart}"
        f"{leads_chart}"
        f"<section class=\"panel\"><h3>Ultimas Guias</h3>{guide_table}</section>"
    )

    return _render_layout("dashboard", "Dashboard Operativo", "Panel administrativo general con estadisticas y monitoreo por modelo.", content, msg, kind, request=request, current_role=role_value)


@router.post("/geo/sync-sepomex")
def backend_sync_sepomex_now(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24", "forzar sincronizacion SEPOMEX")
    if forbidden:
        return forbidden
    try:
        changed = sync_sepomex_catalog(db, force=True)
        colonies = db.query(func.count(GeoColony.id)).scalar() or 0
        return _redirect(
            "/ERPMande24",
            f"Sync SEPOMEX ejecutada. cambios={changed}. colonias={colonies}.",
        )
    except Exception as exc:
        db.rollback()
        return _redirect("/ERPMande24", f"Error en sync SEPOMEX: {exc}", "error")


@router.get("/guides/new", response_class=HTMLResponse)
def backend_new_guide_page(db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    services = db.query(Service).filter(Service.active.is_(True)).order_by(Service.name.asc()).all()
    stations = db.query(Station).filter(Station.active.is_(True)).order_by(Station.name.asc()).all()
    origin_clients = (
        db.query(ClientProfile)
        .filter(ClientProfile.active.is_(True), ClientProfile.client_kind.in_([ClientKind.origin, ClientKind.both]))
        .order_by(ClientProfile.display_name.asc())
        .all()
    )
    destination_clients = (
        db.query(ClientProfile)
        .filter(ClientProfile.active.is_(True), ClientProfile.client_kind.in_([ClientKind.destination, ClientKind.both]))
        .order_by(ClientProfile.display_name.asc())
        .all()
    )

    service_options = "".join([f'<option value="{item.id}">{escape(item.name)} ({item.service_type.value})</option>' for item in services])
    station_options = "".join([f'<option value="{item.id}">{escape(item.name)}</option>' for item in stations])
    origin_client_options = "".join([f'<option value="{item.id}">{escape(item.display_name)}</option>' for item in origin_clients])
    destination_client_options = "".join([f'<option value="{item.id}">{escape(item.display_name)}</option>' for item in destination_clients])

    catalog_hint = ""
    if not services or not stations:
        catalog_hint = '<p class="msg error">No hay servicios o estaciones activas. Usa "Generar datos demo" para iniciar rapido.</p>'

    content = (
        "<section class=\"panel\"><h3>Captura de Guia</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/guides/create\">"
        "<label>Nombre cliente<input name=\"customer_name\" minlength=\"2\" maxlength=\"150\" value=\"Cliente Backend\" required /></label>"
        "<label>Nombre destino<input name=\"destination_name\" minlength=\"2\" maxlength=\"150\" value=\"Destino Backend\" required /></label>"
        f"<label>Cliente origen<select name=\"origin_client_id\"><option value=\"\">Selecciona (opcional)</option>{origin_client_options}</select></label>"
        f"<label>Cliente destino<select name=\"destination_client_id\"><option value=\"\">Selecciona (opcional)</option>{destination_client_options}</select></label>"
        "<label>Facturar servicio origen<select name=\"origin_wants_invoice\"><option value=\"\">Tomar perfil</option><option value=\"true\">Si</option><option value=\"false\">No</option></select></label>"
        f"<label>Servicio<select name=\"service_id\" required><option value=\"\">Selecciona</option>{service_options}</select></label>"
        f"<label>Estacion<select name=\"station_id\" required><option value=\"\">Selecciona</option>{station_options}</select></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Generar Guia</button></div>"
        "</form>"
        "<div class=\"actions\"><form method=\"post\" action=\"/ERPMande24/demo/seed/form\"><button type=\"submit\">Generar datos demo</button></form>"
        "<a class=\"btn\" href=\"/ERPMande24/guides\">Ver listado de guias</a></div>"
        f"{catalog_hint}</section>"
    )

    return _render_layout("guides_new", "Generar Guia", "Formulario backend para crear guias con precio automatico por tarifario.", content, msg, kind)


@router.post("/guides/create")
def backend_create_guide(
    customer_name: str = Form(...),
    destination_name: str = Form(...),
    origin_client_id: str = Form(""),
    destination_client_id: str = Form(""),
    origin_wants_invoice: str = Form(""),
    service_id: str = Form(...),
    station_id: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_ops(request, "/ERPMande24/guides/new", "crear guia")
    if forbidden:
        return forbidden
    service = db.query(Service).filter(Service.id == service_id, Service.active.is_(True)).first()
    if not service:
        return _redirect("/ERPMande24/guides/new", "Servicio no encontrado o inactivo.", "error")

    station = db.query(Station).filter(Station.id == station_id, Station.active.is_(True)).first()
    if not station:
        return _redirect("/ERPMande24/guides/new", "Estacion no encontrada o inactiva.", "error")

    pricing_rule = (
        db.query(PricingRule)
        .filter(
            PricingRule.service_id == service_id,
            PricingRule.station_id == station_id,
            PricingRule.active.is_(True),
        )
        .first()
    )
    if not pricing_rule:
        return _redirect("/ERPMande24/guides/new", "No existe tarifa activa para servicio + estacion.", "error")

    origin_client = None
    destination_client = None
    if origin_client_id.strip():
        origin_client = db.query(ClientProfile).filter(ClientProfile.id == origin_client_id.strip(), ClientProfile.active.is_(True)).first()
        if not origin_client:
            return _redirect("/ERPMande24/guides/new", "Cliente origen no encontrado o inactivo.", "error")
    if destination_client_id.strip():
        destination_client = db.query(ClientProfile).filter(ClientProfile.id == destination_client_id.strip(), ClientProfile.active.is_(True)).first()
        if not destination_client:
            return _redirect("/ERPMande24/guides/new", "Cliente destino no encontrado o inactivo.", "error")

    wants_invoice = origin_client.wants_invoice if origin_client else False
    if origin_wants_invoice in {"true", "false"}:
        wants_invoice = origin_wants_invoice == "true"

    guide_code = f"M24-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    guide = Guide(
        guide_code=guide_code,
        customer_name=(origin_client.display_name if origin_client else customer_name.strip()),
        destination_name=(destination_client.display_name if destination_client else destination_name.strip()),
        service_type=service.service_type.value,
        service_id=service.id,
        station_id=station.id,
        sale_amount=pricing_rule.price,
        currency=pricing_rule.currency,
    )
    db.add(guide)
    db.flush()

    delivery = Delivery(guide_id=guide.id, stage=WorkflowStage.assigned)
    db.add(delivery)
    db.add(
        GuideParty(
            guide_id=guide.id,
            origin_client_id=(origin_client.id if origin_client else None),
            destination_client_id=(destination_client.id if destination_client else None),
            origin_wants_invoice=wants_invoice,
        )
    )
    db.commit()

    return _redirect(
        "/ERPMande24/guides/new",
        f"Guia {guide.guide_code} creada con delivery {delivery.id} ({guide.sale_amount:.2f} {guide.currency}).",
        "ok",
    )


@router.get("/guides", response_class=HTMLResponse)
def backend_guides(
    request: Request,
    db: Session = Depends(get_db),
    q: str = "",
    page: int = 1,
    page_size: int = 25,
    msg: str = "",
    kind: str = "ok",
) -> str:
    safe_page = max(1, page)
    safe_page_size = max(5, min(page_size, 100))
    guides_query = db.query(Guide)
    if q.strip():
        term = f"%{q.strip()}%"
        guides_query = guides_query.filter(
            Guide.guide_code.ilike(term)
            | Guide.customer_name.ilike(term)
            | Guide.destination_name.ilike(term)
        )

    total = guides_query.count()
    offset = (safe_page - 1) * safe_page_size
    guides = guides_query.order_by(Guide.created_at.desc()).offset(offset).limit(safe_page_size).all()
    rows = []
    for item in guides:
        rows.append(
            [
                f'<a href="/ERPMande24/guides/{escape(item.guide_code)}">{escape(item.guide_code)}</a>',
                escape(item.customer_name),
                escape(item.destination_name),
                escape(item.service_type),
                f"{item.sale_amount:.2f} {escape(item.currency)}",
                item.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    pager = _pagination(
        "/ERPMande24/guides",
        safe_page,
        safe_page_size,
        total,
        query_params={"q": q.strip()} if q.strip() else None,
    )

    content = (
        "<section class=\"panel\"><h3>Listado de Guias</h3>"
        f"{_querybox('/ERPMande24/guides', 'Buscar por guia, cliente o destino', q)}"
        f"{pager}"
        "<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/guides.csv\">Exportar CSV</a></div>"
        f"{_table(['Guia', 'Cliente', 'Destino', 'Tipo Servicio', 'Monto', 'Creada'], rows)}"
        f"{pager}</section>"
    )
    return _render_layout("guides", "Guias", "Vista tipo lista del modelo Guide.", content, msg, kind, request=request)


@router.get("/guides/{guide_code}", response_class=HTMLResponse)
def backend_guide_detail(guide_code: str, request: Request, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    guide = db.query(Guide).filter(Guide.guide_code == guide_code).first()
    if not guide:
        return _render_layout("guides", "Guia", "Detalle", '<section class="panel"><div class="empty">Guia no encontrada.</div></section>', msg, "error", request=request)

    deliveries = db.query(Delivery).filter(Delivery.guide_id == guide.id).order_by(Delivery.created_at.asc()).all()
    delivery_rows = [
        [
            f'<a href="/ERPMande24/deliveries/{escape(item.id)}">{escape(item.id)}</a>',
            escape(item.stage.value),
            "si" if item.has_evidence else "no",
            "si" if item.has_signature else "no",
            item.updated_at.strftime("%Y-%m-%d %H:%M"),
        ]
        for item in deliveries
    ]

    timeline_events = [(guide.created_at.strftime("%Y-%m-%d %H:%M"), f"Guia creada ({guide.guide_code})")]
    for item in deliveries:
        label = f"Delivery {item.id} -> {item.stage.value}"
        if item.delivered_at:
            label = f"{label} (entregada)"
        timeline_events.append((item.updated_at.strftime("%Y-%m-%d %H:%M"), label))

    details = (
        f"{_tabs([('resumen', 'Resumen'), ('entregas', 'Entregas'), ('timeline', 'Timeline'), ('operacion', 'Operacion')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Guia</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>Codigo</small><strong>{escape(guide.guide_code)}</strong></article>"
        f"<article class=\"kpi\"><small>Cliente</small><strong>{escape(guide.customer_name)}</strong></article>"
        f"<article class=\"kpi\"><small>Destino</small><strong>{escape(guide.destination_name)}</strong></article>"
        f"<article class=\"kpi\"><small>Monto</small><strong>{guide.sale_amount:.2f} {escape(guide.currency)}</strong></article>"
        "</div></section>"
        "<section id=\"operacion\" class=\"panel\"><h3>Operacion</h3><div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/guides\">Volver a listado</a><a class=\"btn\" href=\"/ERPMande24/guides/new\">Nueva Guia</a></div></section>"
    )
    content = (
        details
        + f"<section id=\"entregas\" class=\"panel\"><h3>Entregas de la Guia</h3>{_table(['Delivery ID', 'Etapa', 'Evidencia', 'Firma', 'Actualizada'], delivery_rows)}</section>"
        + f"<section id=\"timeline\" class=\"panel\"><h3>Timeline</h3>{_timeline(timeline_events)}</section>"
    )
    return _render_layout("guides", f"Guia {guide.guide_code}", "Vista detalle tipo formulario.", content, msg, kind, request=request)


@router.get("/deliveries", response_class=HTMLResponse)
def backend_deliveries(
    request: Request,
    db: Session = Depends(get_db),
    q: str = "",
    stage: str = "",
    page: int = 1,
    page_size: int = 25,
    msg: str = "",
    kind: str = "ok",
) -> str:
    safe_page = max(1, page)
    safe_page_size = max(5, min(page_size, 100))
    deliveries_query = db.query(Delivery)
    if q.strip():
        term = f"%{q.strip()}%"
        deliveries_query = deliveries_query.join(Guide).filter(
            Delivery.id.ilike(term) | Guide.guide_code.ilike(term)
        )
    if stage.strip():
        try:
            deliveries_query = deliveries_query.filter(Delivery.stage == WorkflowStage(stage.strip()))
        except ValueError:
            pass

    total = deliveries_query.count()
    offset = (safe_page - 1) * safe_page_size
    deliveries = deliveries_query.order_by(Delivery.updated_at.desc()).offset(offset).limit(safe_page_size).all()
    rows = []
    for item in deliveries:
        rows.append(
            [
                f'<a href="/ERPMande24/deliveries/{escape(item.id)}">{escape(item.id)}</a>',
                f'<a href="/ERPMande24/guides/{escape(item.guide.guide_code if item.guide else "")}">{escape(item.guide.guide_code if item.guide else "-")}</a>',
                f"<span class=\"badge\">{escape(item.stage.value)}</span>",
                "si" if item.has_evidence else "no",
                "si" if item.has_signature else "no",
                item.updated_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    form = (
        "<section class=\"panel\"><h3>Actualizar Etapa de Entrega</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/deliveries/stage\">"
        "<label>Delivery ID<input name=\"delivery_id\" required /></label>"
        "<label>Etapa<select name=\"stage\">"
        "<option value=\"assigned\">assigned</option><option value=\"picked_up\">picked_up</option>"
        "<option value=\"in_transit\">in_transit</option><option value=\"at_station\">at_station</option>"
        "<option value=\"out_for_delivery\">out_for_delivery</option><option value=\"delivered\">delivered</option>"
        "<option value=\"failed\">failed</option></select></label>"
        "<label class=\"full\">Nota<textarea name=\"note\" placeholder=\"Opcional\"></textarea></label>"
        "<label><input type=\"checkbox\" name=\"has_evidence\" /> Tiene evidencia</label>"
        "<label><input type=\"checkbox\" name=\"has_signature\" /> Tiene firma</label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Actualizar</button></div>"
        "</form></section>"
    )

    stage_options = "".join(
        [
            f'<option value="{item.value}" {"selected" if stage == item.value else ""}>{item.value}</option>'
            for item in WorkflowStage
        ]
    )

    filter_box = (
        "<section class=\"panel\"><h3>Filtros</h3>"
        "<form class=\"actions\" method=\"get\" action=\"/ERPMande24/deliveries\">"
        f'<input name="q" value="{escape(q)}" placeholder="Buscar por delivery o guia" />'
        f'<select name="stage"><option value="">Todas las etapas</option>{stage_options}</select>'
        "<button type=\"submit\">Aplicar</button>"
        "<a class=\"btn\" href=\"/ERPMande24/deliveries\">Limpiar</a>"
        "</form></section>"
    )

    pager_params: dict[str, str] = {}
    if q.strip():
        pager_params["q"] = q.strip()
    if stage.strip():
        pager_params["stage"] = stage.strip()
    pager = _pagination("/ERPMande24/deliveries", safe_page, safe_page_size, total, query_params=pager_params or None)

    content = (
        filter_box
        + form
        + "<section class=\"panel\"><h3>Listado de Entregas</h3>"
        + pager
        + "<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/deliveries.csv\">Exportar CSV</a></div>"
        + _table(['Delivery ID', 'Guia', 'Etapa', 'Evidencia', 'Firma', 'Actualizada'], rows)
        + pager
        + "</section>"
    )
    return _render_layout("deliveries", "Entregas", "Control de estado y trazabilidad de deliveries.", content, msg, kind, request=request)


@router.get("/deliveries/{delivery_id}", response_class=HTMLResponse)
def backend_delivery_detail(delivery_id: str, request: Request, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    item = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not item:
        return _render_layout("deliveries", "Entrega", "Detalle", '<section class="panel"><div class="empty">Entrega no encontrada.</div></section>', msg, "error", request=request)

    timeline_events = [(item.created_at.strftime("%Y-%m-%d %H:%M"), f"Delivery creado ({item.id})")]
    if item.delivered_at:
        timeline_events.append((item.delivered_at.strftime("%Y-%m-%d %H:%M"), "Marcada como delivered"))
    if item.note:
        timeline_events.append((item.updated_at.strftime("%Y-%m-%d %H:%M"), f"Nota: {item.note}"))
    timeline_events.append((item.updated_at.strftime("%Y-%m-%d %H:%M"), f"Etapa actual: {item.stage.value}"))

    details = (
        f"{_tabs([('resumen', 'Resumen'), ('timeline', 'Timeline'), ('operacion', 'Operacion')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Entrega</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>Delivery ID</small><strong>{escape(item.id)}</strong></article>"
        f"<article class=\"kpi\"><small>Guia</small><strong><a href=\"/ERPMande24/guides/{escape(item.guide.guide_code if item.guide else '')}\">{escape(item.guide.guide_code if item.guide else '-')}</a></strong></article>"
        f"<article class=\"kpi\"><small>Etapa</small><strong>{escape(item.stage.value)}</strong></article>"
        f"<article class=\"kpi\"><small>Evidencia/Firma</small><strong>{'si' if item.has_evidence else 'no'} / {'si' if item.has_signature else 'no'}</strong></article>"
        "</div></section>"
        f"<section id=\"timeline\" class=\"panel\"><h3>Timeline</h3>{_timeline(timeline_events)}</section>"
        "<section id=\"operacion\" class=\"panel\"><h3>Operacion</h3><div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/deliveries\">Volver a entregas</a></div></section>"
    )
    return _render_layout("deliveries", f"Entrega {item.id}", "Vista detalle tipo formulario.", details, msg, kind, request=request)


@router.post("/deliveries/stage")
def backend_update_delivery_stage(
    delivery_id: str = Form(...),
    stage: str = Form(...),
    note: str = Form(""),
    has_evidence: str | None = Form(None),
    has_signature: str | None = Form(None),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_ops(request, "/ERPMande24/deliveries", "actualizar entrega")
    if forbidden:
        return forbidden
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id.strip()).first()
    if not delivery:
        return _redirect("/ERPMande24/deliveries", "Delivery no encontrado.", "error")

    try:
        new_stage = WorkflowStage(stage)
    except ValueError:
        return _redirect("/ERPMande24/deliveries", "Etapa no valida.", "error")

    ev = has_evidence == "on"
    sg = has_signature == "on"
    if new_stage == WorkflowStage.delivered and not (ev and sg):
        return _redirect("/ERPMande24/deliveries", "Para delivered se requiere evidencia y firma.", "error")

    delivery.stage = new_stage
    delivery.note = note.strip() if note else None
    delivery.has_evidence = ev
    delivery.has_signature = sg
    if new_stage == WorkflowStage.delivered and not delivery.delivered_at:
        delivery.delivered_at = datetime.now(timezone.utc)
    delivery.updated_at = datetime.now(timezone.utc)
    db.commit()

    return _redirect("/ERPMande24/deliveries", f"Delivery {delivery.id} actualizado a {delivery.stage.value}.")


@router.get("/catalogs/services", response_class=HTMLResponse)
def backend_services(db: Session = Depends(get_db), q: str = "", msg: str = "", kind: str = "ok") -> str:
    services_query = db.query(Service)
    if q.strip():
        services_query = services_query.filter(Service.name.ilike(f"%{q.strip()}%"))
    services = services_query.order_by(Service.name.asc()).all()
    rows = [
        [
            f'<input type="checkbox" name="ids" value="{escape(item.id)}" form="bulk-services" />',
            escape(item.id),
            f'<a href="/ERPMande24/catalogs/services/{escape(item.id)}">{escape(item.name)}</a>',
            escape(item.service_type.value),
            "activo" if item.active else "inactivo",
            (
                f'<form class="inline-form" method="post" action="/ERPMande24/catalogs/services/{escape(item.id)}/toggle">'
                f'<input type="hidden" name="active" value="{"false" if item.active else "true"}" />'
                f'<button type="submit">{"Desactivar" if item.active else "Activar"}</button></form>'
            ),
        ]
        for item in services
    ]

    form = (
        "<section class=\"panel\"><h3>Nuevo Servicio</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/services/create\">"
        "<label>Nombre<input name=\"name\" required minlength=\"2\" maxlength=\"120\" /></label>"
        "<label>Tipo<select name=\"service_type\"><option value=\"messaging\">messaging</option><option value=\"package\">package</option><option value=\"errand\">errand</option></select></label>"
        "<label class=\"full\">Descripcion<textarea name=\"description\"></textarea></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Crear Servicio</button></div>"
        "</form></section>"
    )

    content = form + f"<section class=\"panel\"><h3>Lista de Servicios</h3>{_querybox('/ERPMande24/catalogs/services', 'Buscar servicio por nombre', q)}<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/services.csv\">Exportar CSV</a></div>{_bulk_form('bulk-services', '/ERPMande24/catalogs/services/bulk-toggle', 'Aplicar cambios')}{_table(['Sel', 'ID', 'Nombre', 'Tipo', 'Estado', 'Accion'], rows)}</section>"
    return _render_layout("services", "Catalogo de Servicios", "Mantenimiento de servicios operativos.", content, msg, kind)


@router.get("/catalogs/services/{service_id}", response_class=HTMLResponse)
def backend_service_detail(service_id: str, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        return _render_layout("services", "Servicio", "Detalle", '<section class="panel"><div class="empty">Servicio no encontrado.</div></section>', msg, "error")
    content = (
        f"{_tabs([('resumen', 'Resumen'), ('operacion', 'Operacion')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Servicio</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>ID</small><strong>{escape(service.id)}</strong></article>"
        f"<article class=\"kpi\"><small>Nombre</small><strong>{escape(service.name)}</strong></article>"
        f"<article class=\"kpi\"><small>Tipo</small><strong>{escape(service.service_type.value)}</strong></article>"
        f"<article class=\"kpi\"><small>Estado</small><strong>{'activo' if service.active else 'inactivo'}</strong></article>"
        "</div></section>"
        "<section id=\"operacion\" class=\"panel\"><h3>Operacion</h3><div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/catalogs/services\">Volver a servicios</a></div></section>"
    )
    return _render_layout("services", f"Servicio {service.name}", "Vista detalle tipo formulario.", content, msg, kind)


@router.post("/catalogs/services/{service_id}/toggle")
def backend_toggle_service(
    service_id: str,
    active: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/services", "editar servicio")
    if forbidden:
        return forbidden
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        return _redirect("/ERPMande24/catalogs/services", "Servicio no encontrado.", "error")
    service.active = active == "true"
    db.commit()
    return _redirect("/ERPMande24/catalogs/services", f"Servicio {service.name} actualizado a {'activo' if service.active else 'inactivo'}.")


@router.post("/catalogs/services/bulk-toggle")
def backend_bulk_toggle_services(
    ids: list[str] = Form(default=[]),
    active: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/services", "editar servicios")
    if forbidden:
        return forbidden
    if not ids:
        return _redirect("/ERPMande24/catalogs/services", "Selecciona al menos un servicio.", "error")
    value = active == "true"
    updated = db.query(Service).filter(Service.id.in_(ids)).update({Service.active: value}, synchronize_session=False)
    db.commit()
    return _redirect("/ERPMande24/catalogs/services", f"Servicios actualizados: {updated}.")


@router.post("/catalogs/services/create")
def backend_create_service(
    name: str = Form(...),
    service_type: str = Form("messaging"),
    description: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/services", "crear servicio")
    if forbidden:
        return forbidden
    if db.query(Service).filter(Service.name == name.strip()).first():
        return _redirect("/ERPMande24/catalogs/services", "Ya existe un servicio con ese nombre.", "error")

    try:
        stype = ServiceType(service_type)
    except ValueError:
        return _redirect("/ERPMande24/catalogs/services", "Tipo de servicio no valido.", "error")

    service = Service(name=name.strip(), description=(description.strip() or None), service_type=stype, active=True)
    db.add(service)
    db.commit()
    return _redirect("/ERPMande24/catalogs/services", f"Servicio {service.name} creado.")


@router.get("/catalogs/zones", response_class=HTMLResponse)
def backend_zones(db: Session = Depends(get_db), q: str = "", msg: str = "", kind: str = "ok") -> str:
    zones_query = db.query(Zone)
    if q.strip():
        term = f"%{q.strip()}%"
        zones_query = zones_query.filter(Zone.name.ilike(term) | Zone.code.ilike(term))
    zones = zones_query.order_by(Zone.name.asc()).all()
    rows = [
        [
            f'<input type="checkbox" name="ids" value="{escape(item.id)}" form="bulk-zones" />',
            escape(item.id),
            f'<a href="/ERPMande24/catalogs/zones/{escape(item.id)}">{escape(item.name)}</a>',
            escape(item.code),
            "activo" if item.active else "inactivo",
            (
                f'<form class="inline-form" method="post" action="/ERPMande24/catalogs/zones/{escape(item.id)}/toggle">'
                f'<input type="hidden" name="active" value="{"false" if item.active else "true"}" />'
                f'<button type="submit">{"Desactivar" if item.active else "Activar"}</button></form>'
            ),
        ]
        for item in zones
    ]

    form = (
        "<section class=\"panel\"><h3>Nueva Zona</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/zones/create\">"
        "<label>Nombre<input name=\"name\" required minlength=\"2\" maxlength=\"120\" /></label>"
        "<label>Codigo<input name=\"code\" required minlength=\"2\" maxlength=\"30\" /></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Crear Zona</button></div>"
        "</form></section>"
    )

    content = form + f"<section class=\"panel\"><h3>Lista de Zonas</h3>{_querybox('/ERPMande24/catalogs/zones', 'Buscar por nombre o codigo', q)}<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/zones.csv\">Exportar CSV</a></div>{_bulk_form('bulk-zones', '/ERPMande24/catalogs/zones/bulk-toggle', 'Aplicar cambios')}{_table(['Sel', 'ID', 'Nombre', 'Codigo', 'Estado', 'Accion'], rows)}</section>"
    return _render_layout("zones", "Catalogo de Zonas", "Mantenimiento de zonas logisticas.", content, msg, kind)


@router.post("/catalogs/zones/{zone_id}/toggle")
def backend_toggle_zone(zone_id: str, active: str = Form(...), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/zones", "editar zona")
    if forbidden:
        return forbidden
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        return _redirect("/ERPMande24/catalogs/zones", "Zona no encontrada.", "error")
    zone.active = active == "true"
    db.commit()
    return _redirect("/ERPMande24/catalogs/zones", f"Zona {zone.name} actualizada a {'activa' if zone.active else 'inactiva'}.")


@router.post("/catalogs/zones/bulk-toggle")
def backend_bulk_toggle_zones(
    ids: list[str] = Form(default=[]),
    active: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/zones", "editar zonas")
    if forbidden:
        return forbidden
    if not ids:
        return _redirect("/ERPMande24/catalogs/zones", "Selecciona al menos una zona.", "error")
    value = active == "true"
    updated = db.query(Zone).filter(Zone.id.in_(ids)).update({Zone.active: value}, synchronize_session=False)
    db.commit()
    return _redirect("/ERPMande24/catalogs/zones", f"Zonas actualizadas: {updated}.")


@router.get("/catalogs/zones/{zone_id}", response_class=HTMLResponse)
def backend_zone_detail(zone_id: str, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        return _render_layout("zones", "Zona", "Detalle", '<section class="panel"><div class="empty">Zona no encontrada.</div></section>', msg, "error")
    stations = db.query(Station).filter(Station.zone_id == zone.id).order_by(Station.name.asc()).all()
    states = db.query(GeoState).order_by(GeoState.name.asc()).all()
    coverage = db.query(ZoneGeoRule).filter(ZoneGeoRule.zone_id == zone.id).order_by(ZoneGeoRule.id.desc()).all()
    state_map = {item.code: item for item in states}
    municipality_codes = [item.municipality_code for item in coverage if item.municipality_code]
    municipality_map = {}
    if municipality_codes:
        municipality_map = {
            item.code: item for item in db.query(GeoMunicipality).filter(GeoMunicipality.code.in_(municipality_codes)).all()
        }
    colony_ids = [item.colony_id for item in coverage if item.colony_id]
    colony_map = {}
    if colony_ids:
        colony_map = {item.id: item for item in db.query(GeoColony).filter(GeoColony.id.in_(colony_ids)).all()}
    station_rows = [[escape(item.id), f'<a href="/ERPMande24/catalogs/stations/{escape(item.id)}">{escape(item.name)}</a>', "activa" if item.active else "inactiva"] for item in stations]
    content = (
        f"{_tabs([('resumen', 'Resumen'), ('relacionados', 'Relacionados'), ('cobertura', 'Cobertura Geo')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Zona</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>ID</small><strong>{escape(zone.id)}</strong></article>"
        f"<article class=\"kpi\"><small>Nombre</small><strong>{escape(zone.name)}</strong></article>"
        f"<article class=\"kpi\"><small>Codigo</small><strong>{escape(zone.code)}</strong></article>"
        f"<article class=\"kpi\"><small>Estado</small><strong>{'activa' if zone.active else 'inactiva'}</strong></article>"
        "</div></section>"
    )
    content += f"<section id=\"relacionados\" class=\"panel\"><h3>Estaciones en la Zona</h3>{_table(['ID', 'Nombre', 'Estado'], station_rows)}</section>"

    state_options = "".join([f'<option value="{escape(item.code)}">{escape(item.name)}</option>' for item in states])
    coverage_rows = []
    for item in coverage:
        state = state_map.get(item.state_code)
        municipality = municipality_map.get(item.municipality_code) if item.municipality_code else None
        colony = colony_map.get(item.colony_id) if item.colony_id else None
        coverage_rows.append(
            [
                escape(state.name if state else item.state_code),
                escape(municipality.name if municipality else (item.municipality_code or "*")),
                escape(item.postal_code or "*"),
                escape(colony.name if colony else "*"),
                (
                    f'<form class="inline-form" method="post" action="/ERPMande24/catalogs/zones/{escape(zone.id)}/coverage/{escape(item.id)}/delete">'
                    f'<button type="submit">Quitar</button></form>'
                ),
            ]
        )

    content += (
        "<section id=\"cobertura\" class=\"panel\"><h3>Cobertura Geografica</h3>"
        f"<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/zones/{escape(zone.id)}/coverage/add\">"
        f"<label>Estado<select id=\"zone-state\" name=\"state_code\" required><option value=\"\">Selecciona</option>{state_options}</select></label>"
        "<label>Municipio<select id=\"zone-municipality\" name=\"municipality_code\"><option value=\"\">Todos</option></select></label>"
        "<label>Codigo postal<select id=\"zone-postal\" name=\"postal_code\"><option value=\"\">Todos</option></select></label>"
        "<label>Colonia<select id=\"zone-colony\" name=\"colony_id\"><option value=\"\">Todas</option></select></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Agregar cobertura</button></div>"
        "</form>"
        f"{_table(['Estado', 'Municipio', 'CP', 'Colonia', 'Accion'], coverage_rows)}"
        "</section>"
        """
<script>
(() => {
  const stateEl = document.getElementById('zone-state');
  const munEl = document.getElementById('zone-municipality');
  const postalEl = document.getElementById('zone-postal');
  const colonyEl = document.getElementById('zone-colony');
  if (!stateEl || !munEl || !postalEl || !colonyEl) return;

  const setRows = (el, rows, placeholder, valueKey = 'code', labelKey = 'name') => {
    el.innerHTML = '';
    const all = document.createElement('option');
    all.value = '';
    all.textContent = placeholder;
    el.appendChild(all);
    rows.forEach((row) => {
      const opt = document.createElement('option');
      opt.value = row[valueKey];
      opt.textContent = row[labelKey] || row[valueKey];
      el.appendChild(opt);
    });
  };

  stateEl.addEventListener('change', async () => {
    setRows(munEl, [], 'Todos');
    setRows(postalEl, [], 'Todos');
    setRows(colonyEl, [], 'Todas');
    if (!stateEl.value) return;
    const data = await fetch(`/ERPMande24/geo/municipalities?state_code=${encodeURIComponent(stateEl.value)}`).then((r) => r.json());
    setRows(munEl, data, 'Todos');
  });

  munEl.addEventListener('change', async () => {
    setRows(postalEl, [], 'Todos');
    setRows(colonyEl, [], 'Todas');
    if (!munEl.value) return;
    const data = await fetch(`/ERPMande24/geo/postal-codes?municipality_code=${encodeURIComponent(munEl.value)}`).then((r) => r.json());
    setRows(postalEl, data, 'Todos', 'code', 'code');
  });

  postalEl.addEventListener('change', async () => {
    setRows(colonyEl, [], 'Todas');
    if (!postalEl.value || !stateEl.value || !munEl.value) return;
    const q = `state_code=${encodeURIComponent(stateEl.value)}&municipality_code=${encodeURIComponent(munEl.value)}&postal_code=${encodeURIComponent(postalEl.value)}`;
    const data = await fetch(`/ERPMande24/geo/colonies?${q}`).then((r) => r.json());
    setRows(colonyEl, data, 'Todas', 'id', 'name');
  });
})();
</script>
"""
    )
    return _render_layout("zones", f"Zona {zone.name}", "Vista detalle tipo formulario.", content, msg, kind)


@router.post("/catalogs/zones/{zone_id}/coverage/add")
def backend_zone_add_coverage(
    zone_id: str,
    state_code: str = Form(...),
    municipality_code: str = Form(""),
    postal_code: str = Form(""),
    colony_id: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, f"/ERPMande24/catalogs/zones/{zone_id}", "editar cobertura de zona")
    if forbidden:
        return forbidden

    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        return _redirect("/ERPMande24/catalogs/zones", "Zona no encontrada.", "error")

    state_value = state_code.strip().upper()
    municipality_value = municipality_code.strip().upper() or None
    postal_value = postal_code.strip() or None
    colony_value = colony_id.strip() or None

    if not db.query(GeoState).filter(GeoState.code == state_value).first():
        return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Estado no valido.", "error")

    if municipality_value and not db.query(GeoMunicipality).filter(GeoMunicipality.code == municipality_value, GeoMunicipality.state_code == state_value).first():
        return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Municipio no valido para ese estado.", "error")

    if postal_value and municipality_value:
        if not db.query(GeoPostalCode).filter(GeoPostalCode.code == postal_value, GeoPostalCode.municipality_code == municipality_value).first():
            return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Codigo postal no valido para ese municipio.", "error")

    if colony_value and municipality_value and postal_value:
        if not db.query(GeoColony).filter(
            GeoColony.id == colony_value,
            GeoColony.state_code == state_value,
            GeoColony.municipality_code == municipality_value,
            GeoColony.postal_code == postal_value,
        ).first():
            return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Colonia no valida para esa cobertura.", "error")

    exists = db.query(ZoneGeoRule).filter(
        ZoneGeoRule.zone_id == zone_id,
        ZoneGeoRule.state_code == state_value,
        ZoneGeoRule.municipality_code == municipality_value,
        ZoneGeoRule.postal_code == postal_value,
        ZoneGeoRule.colony_id == colony_value,
    ).first()
    if exists:
        return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Esa cobertura ya existe.", "error")

    row = ZoneGeoRule(
        zone_id=zone_id,
        state_code=state_value,
        municipality_code=municipality_value,
        postal_code=postal_value,
        colony_id=colony_value,
        active=True,
    )
    db.add(row)
    db.commit()
    return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Cobertura agregada correctamente.")


@router.post("/catalogs/zones/{zone_id}/coverage/{coverage_id}/delete")
def backend_zone_delete_coverage(zone_id: str, coverage_id: str, request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, f"/ERPMande24/catalogs/zones/{zone_id}", "eliminar cobertura de zona")
    if forbidden:
        return forbidden
    row = db.query(ZoneGeoRule).filter(ZoneGeoRule.id == coverage_id, ZoneGeoRule.zone_id == zone_id).first()
    if not row:
        return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Cobertura no encontrada.", "error")
    db.delete(row)
    db.commit()
    return _redirect(f"/ERPMande24/catalogs/zones/{zone_id}", "Cobertura eliminada.")


@router.post("/catalogs/zones/create")
def backend_create_zone(name: str = Form(...), code: str = Form(...), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/zones", "crear zona")
    if forbidden:
        return forbidden
    code_value = code.strip().upper()
    if db.query(Zone).filter(Zone.code == code_value).first():
        return _redirect("/ERPMande24/catalogs/zones", "Ya existe una zona con ese codigo.", "error")

    zone = Zone(name=name.strip(), code=code_value, active=True)
    db.add(zone)
    db.commit()
    return _redirect("/ERPMande24/catalogs/zones", f"Zona {zone.name} creada.")


@router.get("/catalogs/stations", response_class=HTMLResponse)
def backend_stations(db: Session = Depends(get_db), q: str = "", msg: str = "", kind: str = "ok") -> str:
    zones = db.query(Zone).order_by(Zone.name.asc()).all()
    stations_query = db.query(Station)
    if q.strip():
        stations_query = stations_query.filter(Station.name.ilike(f"%{q.strip()}%"))
    stations = stations_query.order_by(Station.name.asc()).all()

    zone_options = "".join([f'<option value="{item.id}">{escape(item.name)} ({escape(item.code)})</option>' for item in zones])
    rows = []
    zone_map = {item.id: item for item in zones}
    for item in stations:
        zone = zone_map.get(item.zone_id)
        zone_label = f"{zone.name} ({zone.code})" if zone else "-"
        rows.append(
            [
                f'<input type="checkbox" name="ids" value="{escape(item.id)}" form="bulk-stations" />',
                escape(item.id),
                f'<a href="/ERPMande24/catalogs/stations/{escape(item.id)}">{escape(item.name)}</a>',
                escape(zone_label),
                "activo" if item.active else "inactivo",
                (
                    f'<form class="inline-form" method="post" action="/ERPMande24/catalogs/stations/{escape(item.id)}/toggle">'
                    f'<input type="hidden" name="active" value="{"false" if item.active else "true"}" />'
                    f'<button type="submit">{"Desactivar" if item.active else "Activar"}</button></form>'
                ),
            ]
        )

    form = (
        "<section class=\"panel\"><h3>Nueva Estacion</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/stations/create\">"
        "<label>Nombre<input name=\"name\" required minlength=\"2\" maxlength=\"120\" /></label>"
        f"<label>Zona<select name=\"zone_id\" required><option value=\"\">Selecciona</option>{zone_options}</select></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Crear Estacion</button></div>"
        "</form></section>"
    )

    content = form + f"<section class=\"panel\"><h3>Lista de Estaciones</h3>{_querybox('/ERPMande24/catalogs/stations', 'Buscar estacion por nombre', q)}<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/stations.csv\">Exportar CSV</a></div>{_bulk_form('bulk-stations', '/ERPMande24/catalogs/stations/bulk-toggle', 'Aplicar cambios')}{_table(['Sel', 'ID', 'Nombre', 'Zona', 'Estado', 'Accion'], rows)}</section>"
    return _render_layout("stations", "Catalogo de Estaciones", "Mantenimiento de estaciones por zona.", content, msg, kind)


@router.post("/catalogs/stations/{station_id}/toggle")
def backend_toggle_station(station_id: str, active: str = Form(...), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/stations", "editar estacion")
    if forbidden:
        return forbidden
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return _redirect("/ERPMande24/catalogs/stations", "Estacion no encontrada.", "error")
    station.active = active == "true"
    db.commit()
    return _redirect("/ERPMande24/catalogs/stations", f"Estacion {station.name} actualizada a {'activa' if station.active else 'inactiva'}.")


@router.post("/catalogs/stations/bulk-toggle")
def backend_bulk_toggle_stations(
    ids: list[str] = Form(default=[]),
    active: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/stations", "editar estaciones")
    if forbidden:
        return forbidden
    if not ids:
        return _redirect("/ERPMande24/catalogs/stations", "Selecciona al menos una estacion.", "error")
    value = active == "true"
    updated = db.query(Station).filter(Station.id.in_(ids)).update({Station.active: value}, synchronize_session=False)
    db.commit()
    return _redirect("/ERPMande24/catalogs/stations", f"Estaciones actualizadas: {updated}.")


@router.get("/catalogs/stations/{station_id}", response_class=HTMLResponse)
def backend_station_detail(station_id: str, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return _render_layout("stations", "Estacion", "Detalle", '<section class="panel"><div class="empty">Estacion no encontrada.</div></section>', msg, "error")
    zone = db.query(Zone).filter(Zone.id == station.zone_id).first()
    guides = db.query(Guide).filter(Guide.station_id == station.id).order_by(Guide.created_at.desc()).limit(20).all()
    guide_rows = [[f'<a href="/ERPMande24/guides/{escape(item.guide_code)}">{escape(item.guide_code)}</a>', escape(item.customer_name), f"{item.sale_amount:.2f} {escape(item.currency)}", item.created_at.strftime("%Y-%m-%d %H:%M")] for item in guides]
    content = (
        f"{_tabs([('resumen', 'Resumen'), ('guias', 'Guias')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Estacion</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>ID</small><strong>{escape(station.id)}</strong></article>"
        f"<article class=\"kpi\"><small>Nombre</small><strong>{escape(station.name)}</strong></article>"
        f"<article class=\"kpi\"><small>Zona</small><strong>{escape(zone.name if zone else '-')}</strong></article>"
        f"<article class=\"kpi\"><small>Estado</small><strong>{'activa' if station.active else 'inactiva'}</strong></article>"
        "</div></section>"
    )
    content += f"<section id=\"guias\" class=\"panel\"><h3>Ultimas Guias de la Estacion</h3>{_table(['Guia', 'Cliente', 'Monto', 'Creada'], guide_rows)}</section>"
    return _render_layout("stations", f"Estacion {station.name}", "Vista detalle tipo formulario.", content, msg, kind)


@router.post("/catalogs/stations/create")
def backend_create_station(name: str = Form(...), zone_id: str = Form(...), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/stations", "crear estacion")
    if forbidden:
        return forbidden
    if not db.query(Zone).filter(Zone.id == zone_id).first():
        return _redirect("/ERPMande24/catalogs/stations", "Zona no encontrada.", "error")

    if db.query(Station).filter(Station.name == name.strip()).first():
        return _redirect("/ERPMande24/catalogs/stations", "Ya existe una estacion con ese nombre.", "error")

    station = Station(name=name.strip(), zone_id=zone_id, active=True)
    db.add(station)
    db.commit()
    return _redirect("/ERPMande24/catalogs/stations", f"Estacion {station.name} creada.")


@router.get("/catalogs/riders", response_class=HTMLResponse)
def backend_riders(db: Session = Depends(get_db), q: str = "", msg: str = "", kind: str = "ok") -> str:
    riders_query = db.query(Rider)
    if q.strip():
        term = f"%{q.strip()}%"
        riders_query = riders_query.join(User, Rider.user_id == User.id).filter(
            Rider.id.ilike(term) | User.full_name.ilike(term) | User.email.ilike(term)
        )
    riders = riders_query.order_by(Rider.id.desc()).limit(200).all()
    users = {item.id: item for item in db.query(User).all()}
    zones = {item.id: item for item in db.query(Zone).all()}
    zone_options = "".join([f'<option value="{escape(item.id)}">{escape(item.name)} ({escape(item.code)})</option>' for item in zones.values()])

    rows = []
    for item in riders:
        user = users.get(item.user_id)
        zone = zones.get(item.zone_id) if item.zone_id else None
        rows.append(
            [
                f'<input type="checkbox" name="ids" value="{escape(item.id)}" form="bulk-riders" />',
                f'<a href="/ERPMande24/catalogs/riders/{escape(item.id)}">{escape(item.id)}</a>',
                escape(user.full_name if user else "-"),
                escape(user.email if user else "-"),
                escape(zone.name if zone else "-"),
                escape(item.vehicle_type),
                escape(item.state.value),
                "activo" if item.active else "inactivo",
                (
                    f'<form class="inline-form" method="post" action="/ERPMande24/catalogs/riders/{escape(item.id)}/toggle">'
                    f'<input type="hidden" name="active" value="{"false" if item.active else "true"}" />'
                    f'<button type="submit">{"Desactivar" if item.active else "Activar"}</button></form>'
                ),
            ]
        )

    create_form = (
        "<section class=\"panel\"><h3>Alta de Rider</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/riders/create\">"
        "<label>Nombre completo<input name=\"full_name\" required minlength=\"2\" maxlength=\"150\" /></label>"
        "<label>Email<input name=\"email\" type=\"email\" required /></label>"
        "<label>Password<input name=\"password\" type=\"password\" required minlength=\"8\" /></label>"
        f"<label>Zona<select name=\"zone_id\"><option value=\"\">Sin zona</option>{zone_options}</select></label>"
        "<label>Vehiculo<input name=\"vehicle_type\" value=\"motorcycle\" minlength=\"2\" maxlength=\"30\" /></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Crear Rider</button></div>"
        "</form></section>"
    )
    content = create_form + f"<section class=\"panel\"><h3>Lista de Riders</h3>{_querybox('/ERPMande24/catalogs/riders', 'Buscar rider por ID, nombre o email', q)}<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/riders.csv\">Exportar CSV</a></div>{_bulk_form('bulk-riders', '/ERPMande24/catalogs/riders/bulk-toggle', 'Aplicar cambios')}{_table(['Sel', 'ID', 'Nombre', 'Email', 'Zona', 'Vehiculo', 'Estado', 'Activo', 'Accion'], rows)}</section>"
    return _render_layout("riders", "Catalogo de Riders", "Vista de riders y su estado operativo.", content, msg, kind)


@router.post("/catalogs/riders/create")
def backend_create_rider(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    zone_id: str = Form(""),
    vehicle_type: str = Form("motorcycle"),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/riders", "crear rider")
    if forbidden:
        return forbidden
    clean_email = email.strip().lower()
    if db.query(User).filter(User.email == clean_email).first():
        return _redirect("/ERPMande24/catalogs/riders", "Ese email ya existe.", "error")

    if zone_id.strip() and not db.query(Zone).filter(Zone.id == zone_id.strip()).first():
        return _redirect("/ERPMande24/catalogs/riders", "Zona no encontrada.", "error")

    user = User(
        email=clean_email,
        full_name=full_name.strip(),
        password_hash=hash_password(password),
        role=UserRole.rider,
        is_active=True,
    )
    db.add(user)
    db.flush()

    rider = Rider(
        user_id=user.id,
        zone_id=zone_id.strip() or None,
        vehicle_type=vehicle_type.strip() or "motorcycle",
        active=True,
    )
    db.add(rider)
    db.commit()
    return _redirect("/ERPMande24/catalogs/riders", f"Rider creado: {rider.id} ({user.email}).")


@router.post("/catalogs/riders/{rider_id}/toggle")
def backend_toggle_rider(rider_id: str, active: str = Form(...), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/riders", "editar rider")
    if forbidden:
        return forbidden
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        return _redirect("/ERPMande24/catalogs/riders", "Rider no encontrado.", "error")
    rider.active = active == "true"
    db.commit()
    return _redirect("/ERPMande24/catalogs/riders", f"Rider {rider.id} actualizado a {'activo' if rider.active else 'inactivo'}.")


@router.post("/catalogs/riders/bulk-toggle")
def backend_bulk_toggle_riders(
    ids: list[str] = Form(default=[]),
    active: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/riders", "editar riders")
    if forbidden:
        return forbidden
    if not ids:
        return _redirect("/ERPMande24/catalogs/riders", "Selecciona al menos un rider.", "error")
    value = active == "true"
    updated = db.query(Rider).filter(Rider.id.in_(ids)).update({Rider.active: value}, synchronize_session=False)
    db.commit()
    return _redirect("/ERPMande24/catalogs/riders", f"Riders actualizados: {updated}.")


@router.get("/catalogs/riders/{rider_id}", response_class=HTMLResponse)
def backend_rider_detail(rider_id: str, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        return _render_layout("riders", "Rider", "Detalle", '<section class="panel"><div class="empty">Rider no encontrado.</div></section>', msg, "error")
    user = db.query(User).filter(User.id == rider.user_id).first()
    zone = db.query(Zone).filter(Zone.id == rider.zone_id).first() if rider.zone_id else None
    deliveries = db.query(Delivery).filter(Delivery.rider_id == rider.id).order_by(Delivery.updated_at.desc()).limit(20).all()
    delivery_rows = [[f'<a href="/ERPMande24/deliveries/{escape(item.id)}">{escape(item.id)}</a>', escape(item.guide.guide_code if item.guide else '-'), escape(item.stage.value), item.updated_at.strftime('%Y-%m-%d %H:%M')] for item in deliveries]
    content = (
        f"{_tabs([('resumen', 'Resumen'), ('entregas', 'Entregas')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Rider</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>ID</small><strong>{escape(rider.id)}</strong></article>"
        f"<article class=\"kpi\"><small>Nombre</small><strong>{escape(user.full_name if user else '-')}</strong></article>"
        f"<article class=\"kpi\"><small>Email</small><strong>{escape(user.email if user else '-')}</strong></article>"
        f"<article class=\"kpi\"><small>Zona</small><strong>{escape(zone.name if zone else '-')}</strong></article>"
        f"<article class=\"kpi\"><small>Vehiculo</small><strong>{escape(rider.vehicle_type)}</strong></article>"
        f"<article class=\"kpi\"><small>Estado</small><strong>{escape(rider.state.value)}</strong></article>"
        "</div></section>"
    )
    content += f"<section id=\"entregas\" class=\"panel\"><h3>Entregas Asignadas</h3>{_table(['Delivery', 'Guia', 'Etapa', 'Actualizada'], delivery_rows)}</section>"
    return _render_layout("riders", f"Rider {rider.id}", "Vista detalle tipo formulario.", content, msg, kind)


@router.get("/geo/municipalities", response_class=JSONResponse)
def backend_geo_municipalities(state_code: str, db: Session = Depends(get_db)) -> JSONResponse:
    rows = (
        db.query(GeoMunicipality)
        .filter(GeoMunicipality.state_code == state_code.strip().upper())
        .order_by(GeoMunicipality.name.asc())
        .all()
    )
    payload = [{"code": item.code, "name": item.name} for item in rows]
    return JSONResponse(payload)


@router.get("/geo/postal-codes", response_class=JSONResponse)
def backend_geo_postal_codes(municipality_code: str, db: Session = Depends(get_db)) -> JSONResponse:
    rows = (
        db.query(GeoPostalCode)
        .filter(GeoPostalCode.municipality_code == municipality_code.strip().upper())
        .order_by(GeoPostalCode.code.asc())
        .all()
    )
    payload = [{"code": item.code} for item in rows]
    return JSONResponse(payload)


@router.get("/geo/colonies", response_class=JSONResponse)
def backend_geo_colonies(state_code: str, municipality_code: str, postal_code: str, db: Session = Depends(get_db)) -> JSONResponse:
    rows = (
        db.query(GeoColony)
        .filter(
            GeoColony.state_code == state_code.strip().upper(),
            GeoColony.municipality_code == municipality_code.strip().upper(),
            GeoColony.postal_code == postal_code.strip(),
        )
        .order_by(GeoColony.name.asc())
        .all()
    )
    payload = [{"id": item.id, "name": item.name, "settlement_type": item.settlement_type} for item in rows]
    return JSONResponse(payload)


@router.get("/catalogs/clients", response_class=HTMLResponse)
def backend_clients(
    db: Session = Depends(get_db),
    q: str = "",
    client_kind: str = "",
    state_code: str = "",
    msg: str = "",
    kind: str = "ok",
) -> str:
    clients_query = db.query(ClientProfile)
    if client_kind in {"origin", "destination", "both"}:
        if client_kind == "origin":
            clients_query = clients_query.filter(ClientProfile.client_kind.in_([ClientKind.origin, ClientKind.both]))
        elif client_kind == "destination":
            clients_query = clients_query.filter(ClientProfile.client_kind.in_([ClientKind.destination, ClientKind.both]))
        else:
            clients_query = clients_query.filter(ClientProfile.client_kind == ClientKind.both)

    if state_code.strip():
        clients_query = clients_query.filter(ClientProfile.state_code == state_code.strip().upper())

    if q.strip():
        term = f"%{q.strip()}%"
        clients_query = clients_query.filter(
            ClientProfile.display_name.ilike(term)
            | ClientProfile.state_code.ilike(term)
            | ClientProfile.municipality_code.ilike(term)
            | ClientProfile.postal_code.ilike(term)
        )

    clients = clients_query.order_by(ClientProfile.created_at.desc()).limit(300).all()
    users = {item.id: item for item in db.query(User).all()}
    states = {item.code: item for item in db.query(GeoState).all()}
    municipalities = {item.code: item for item in db.query(GeoMunicipality).all()}
    postal_codes = {item.code: item for item in db.query(GeoPostalCode).all()}
    colony_ids = [item.colony_id for item in clients if item.colony_id]
    colonies = {}
    if colony_ids:
        colonies = {item.id: item for item in db.query(GeoColony).filter(GeoColony.id.in_(colony_ids)).all()}
    state_options = "".join(
        [
            f'<option value="{escape(item.code)}" {"selected" if item.code == state_code else ""}>{escape(item.name)}</option>'
            for item in sorted(states.values(), key=lambda row: row.name.lower())
        ]
    )
    kind_options = "".join(
        [
            f'<option value="{value}" {"selected" if client_kind == value else ""}>{label}</option>'
            for value, label in [("", "Todos"), ("origin", "Origen"), ("destination", "Destino"), ("both", "Ambos")]
        ]
    )

    export_params = {}
    if q.strip():
        export_params["q"] = q.strip()
    if client_kind in {"origin", "destination", "both"}:
        export_params["client_kind"] = client_kind
    if state_code.strip():
        export_params["state_code"] = state_code.strip().upper()
    export_url = "/ERPMande24/export/clients.csv"
    if export_params:
        export_url = f"{export_url}?{urlencode(export_params)}"

    rows = []
    for item in clients:
        state = states.get(item.state_code)
        municipality = municipalities.get(item.municipality_code)
        postal_code = postal_codes.get(item.postal_code)
        colony = colonies.get(item.colony_id) if item.colony_id else None
        linked_user = users.get(item.user_id) if item.user_id else None
        rows.append(
            [
                escape(item.id),
                escape(item.display_name),
                escape(item.client_kind.value),
                escape(state.name if state else item.state_code),
                escape(municipality.name if municipality else item.municipality_code),
                escape(postal_code.code if postal_code else item.postal_code),
                escape(colony.name if colony else "-"),
                escape(item.address_line or "-"),
                "si" if item.wants_invoice else "no",
                escape(linked_user.email if linked_user else "sin acceso portal"),
                "activo" if item.active else "inactivo",
                f'<a class="btn" href="/ERPMande24/catalogs/clients/{escape(item.id)}">Editar</a>',
            ]
        )

    state_create_options = "".join(
        [f'<option value="{escape(item.code)}">{escape(item.name)}</option>' for item in sorted(states.values(), key=lambda row: row.name.lower())]
    )
    create_form = (
        "<section id=\"nuevo-cliente\" class=\"panel\"><h3>Nuevo Cliente</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/clients/create\">"
        "<label>Nombre cliente<input name=\"display_name\" required minlength=\"2\" maxlength=\"150\" /></label>"
        "<label>Tipo cliente<select name=\"client_kind\"><option value=\"origin\">Origen</option><option value=\"destination\">Destino</option><option value=\"both\">Ambos</option></select></label>"
        f"<label>Estado<select id=\"new-client-state\" name=\"state_code\" required><option value=\"\">Selecciona</option>{state_create_options}</select></label>"
        "<label>Municipio<select id=\"new-client-municipality\" name=\"municipality_code\" required><option value=\"\">Selecciona estado</option></select></label>"
        "<label>Codigo postal<select id=\"new-client-postal\" name=\"postal_code\" required><option value=\"\">Selecciona municipio</option></select></label>"
        "<label>Colonia<select id=\"new-client-colony\" name=\"colony_id\" required><option value=\"\">Selecciona codigo postal</option></select></label>"
        "<label>Direccion<input name=\"address_line\" maxlength=\"255\" /></label>"
        "<label>Facturar servicios origen<select name=\"wants_invoice\"><option value=\"false\">No</option><option value=\"true\">Si</option></select></label>"
        "<label>Crear acceso portal<select name=\"create_portal_access\"><option value=\"false\">No</option><option value=\"true\">Si</option></select></label>"
        "<label>Email portal (si aplica)<input type=\"email\" name=\"portal_email\" /></label>"
        "<label>Password portal (si aplica)<input type=\"password\" name=\"portal_password\" minlength=\"8\" /></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Crear Cliente</button></div>"
        "</form></section>"
    )

    cascade_script = """
<script>
(() => {
    const stateEl = document.getElementById('new-client-state');
    const munEl = document.getElementById('new-client-municipality');
    const postalEl = document.getElementById('new-client-postal');
    const colonyEl = document.getElementById('new-client-colony');
    if (!stateEl || !munEl || !postalEl || !colonyEl) return;

    const setOptions = (el, rows, placeholder, valueKey = 'code', labelKey = 'name') => {
        el.innerHTML = '';
        const first = document.createElement('option');
        first.value = '';
        first.textContent = placeholder;
        el.appendChild(first);
        rows.forEach((row) => {
            const opt = document.createElement('option');
            opt.value = row[valueKey];
            opt.textContent = row[labelKey] || row[valueKey];
            el.appendChild(opt);
        });
    };

    stateEl.addEventListener('change', async () => {
        setOptions(munEl, [], 'Cargando municipios...');
        setOptions(postalEl, [], 'Selecciona municipio');
        setOptions(colonyEl, [], 'Selecciona codigo postal');
        if (!stateEl.value) return setOptions(munEl, [], 'Selecciona estado');
        const data = await fetch(`/ERPMande24/geo/municipalities?state_code=${encodeURIComponent(stateEl.value)}`).then((r) => r.json());
        setOptions(munEl, data, 'Selecciona municipio');
    });

    munEl.addEventListener('change', async () => {
        setOptions(postalEl, [], 'Cargando codigos...');
        setOptions(colonyEl, [], 'Selecciona codigo postal');
        if (!munEl.value) return setOptions(postalEl, [], 'Selecciona municipio');
        const data = await fetch(`/ERPMande24/geo/postal-codes?municipality_code=${encodeURIComponent(munEl.value)}`).then((r) => r.json());
        setOptions(postalEl, data, 'Selecciona codigo postal', 'code', 'code');
    });

    postalEl.addEventListener('change', async () => {
        setOptions(colonyEl, [], 'Cargando colonias...');
        if (!postalEl.value || !stateEl.value || !munEl.value) return setOptions(colonyEl, [], 'Selecciona codigo postal');
        const q = `state_code=${encodeURIComponent(stateEl.value)}&municipality_code=${encodeURIComponent(munEl.value)}&postal_code=${encodeURIComponent(postalEl.value)}`;
        const data = await fetch(`/ERPMande24/geo/colonies?${q}`).then((r) => r.json());
        setOptions(colonyEl, data, 'Selecciona colonia', 'id', 'name');
    });
})();
</script>
"""

    content = (
        "<section class=\"panel\"><h3>Catalogo de Clientes</h3>"
        "<form class=\"actions\" method=\"get\" action=\"/ERPMande24/catalogs/clients\">"
        f"<input name=\"q\" value=\"{escape(q)}\" placeholder=\"Buscar por nombre, estado, municipio o CP\" />"
        f"<select name=\"client_kind\">{kind_options}</select>"
        f"<select name=\"state_code\"><option value=\"\">Todos los estados</option>{state_options}</select>"
        "<button type=\"submit\">Aplicar filtros</button>"
        "<a class=\"btn\" href=\"/ERPMande24/catalogs/clients\">Limpiar</a>"
        "</form>"
        f"<div class=\"actions\"><a class=\"btn primary\" href=\"/ERPMande24/catalogs/clients#nuevo-cliente\">Crear cliente nuevo</a><a class=\"btn\" href=\"{escape(export_url)}\">Exportar CSV</a><a class=\"btn\" href=\"/client\">Abrir Portal Cliente</a><a class=\"btn\" href=\"/station\">Abrir Portal Estacion</a></div>"
        f"{_table(['ID', 'Nombre', 'Tipo', 'Estado', 'Municipio', 'CP', 'Colonia', 'Direccion', 'Factura Origen', 'Usuario Portal', 'Estado Registro', 'Accion'], rows)}"
        "</section>"
    )
    return _render_layout("clients", "Catalogo de Clientes", "Clientes origen y destino con direccion y facturacion.", create_form + content + cascade_script, msg, kind)


@router.post("/catalogs/clients/create")
def backend_create_client(
    display_name: str = Form(...),
    client_kind: str = Form("origin"),
    state_code: str = Form(...),
    municipality_code: str = Form(...),
    postal_code: str = Form(...),
    colony_id: str = Form(...),
    address_line: str = Form(""),
    wants_invoice: str = Form("false"),
    create_portal_access: str = Form("false"),
    portal_email: str = Form(""),
    portal_password: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_ops(request, "/ERPMande24/catalogs/clients", "crear cliente")
    if forbidden:
        return forbidden

    state = db.query(GeoState).filter(GeoState.code == state_code.strip().upper()).first()
    if not state:
        return _redirect("/ERPMande24/catalogs/clients", "Estado no encontrado.", "error")

    municipality = (
        db.query(GeoMunicipality)
        .filter(GeoMunicipality.code == municipality_code.strip().upper(), GeoMunicipality.state_code == state.code)
        .first()
    )
    if not municipality:
        return _redirect("/ERPMande24/catalogs/clients", "Municipio no encontrado para ese estado.", "error")

    postal = (
        db.query(GeoPostalCode)
        .filter(GeoPostalCode.code == postal_code.strip(), GeoPostalCode.municipality_code == municipality.code)
        .first()
    )
    if not postal:
        return _redirect("/ERPMande24/catalogs/clients", "Codigo postal no encontrado para ese municipio.", "error")

    colony = (
        db.query(GeoColony)
        .filter(
            GeoColony.id == colony_id.strip(),
            GeoColony.state_code == state.code,
            GeoColony.municipality_code == municipality.code,
            GeoColony.postal_code == postal.code,
        )
        .first()
    )
    if not colony:
        return _redirect("/ERPMande24/catalogs/clients", "Colonia no encontrada para ese estado/municipio/CP.", "error")

    try:
        kind_value = ClientKind(client_kind)
    except ValueError:
        return _redirect("/ERPMande24/catalogs/clients", "Tipo de cliente no valido.", "error")

    user_id = None
    if create_portal_access == "true":
        clean_email = portal_email.strip().lower()
        if not clean_email or len(portal_password.strip()) < 8:
            return _redirect("/ERPMande24/catalogs/clients", "Para acceso portal captura email y password minimo 8 caracteres.", "error")
        existing = db.query(User).filter(User.email == clean_email).first()
        if existing:
            user_id = existing.id
        else:
            user = User(
                email=clean_email,
                full_name=display_name.strip(),
                password_hash=hash_password(portal_password.strip()),
                role=UserRole.client,
                is_active=True,
            )
            db.add(user)
            db.flush()
            user_id = user.id

    client = ClientProfile(
        user_id=user_id,
        display_name=display_name.strip(),
        client_kind=kind_value,
        state_code=state.code,
        municipality_code=municipality.code,
        postal_code=postal.code,
        colony_id=colony.id,
        address_line=address_line.strip(),
        wants_invoice=(wants_invoice == "true"),
        active=True,
    )
    db.add(client)
    db.commit()
    return _redirect("/ERPMande24/catalogs/clients", f"Cliente {client.display_name} creado.")


@router.get("/catalogs/clients/{client_id}", response_class=HTMLResponse)
def backend_client_detail(client_id: str, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    client = db.query(ClientProfile).filter(ClientProfile.id == client_id).first()
    if not client:
        return _render_layout("clients", "Cliente", "Detalle", '<section class="panel"><div class="empty">Cliente no encontrado.</div></section>', msg, "error")

    states = db.query(GeoState).order_by(GeoState.name.asc()).all()
    municipalities = (
        db.query(GeoMunicipality)
        .filter(GeoMunicipality.state_code == client.state_code)
        .order_by(GeoMunicipality.name.asc())
        .all()
    )
    postals = (
        db.query(GeoPostalCode)
        .filter(GeoPostalCode.municipality_code == client.municipality_code)
        .order_by(GeoPostalCode.code.asc())
        .all()
    )
    colonies = (
        db.query(GeoColony)
        .filter(
            GeoColony.state_code == client.state_code,
            GeoColony.municipality_code == client.municipality_code,
            GeoColony.postal_code == client.postal_code,
        )
        .order_by(GeoColony.name.asc())
        .all()
    )
    linked_user = db.query(User).filter(User.id == client.user_id).first() if client.user_id else None

    state_options = "".join([f'<option value="{escape(item.code)}" {"selected" if item.code == client.state_code else ""}>{escape(item.name)}</option>' for item in states])
    municipality_options = "".join([f'<option value="{escape(item.code)}" {"selected" if item.code == client.municipality_code else ""}>{escape(item.name)}</option>' for item in municipalities])
    postal_options = "".join([f'<option value="{escape(item.code)}" {"selected" if item.code == client.postal_code else ""}>{escape(item.code)}</option>' for item in postals])
    colony_options = "".join([f'<option value="{escape(item.id)}" {"selected" if item.id == client.colony_id else ""}>{escape(item.name)}</option>' for item in colonies])

    content = (
        f"{_tabs([('resumen', 'Resumen'), ('editar', 'Editar')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Cliente</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>ID</small><strong>{escape(client.id)}</strong></article>"
        f"<article class=\"kpi\"><small>Nombre</small><strong>{escape(client.display_name)}</strong></article>"
        f"<article class=\"kpi\"><small>Tipo</small><strong>{escape(client.client_kind.value)}</strong></article>"
        f"<article class=\"kpi\"><small>Portal</small><strong>{escape(linked_user.email if linked_user else 'Sin acceso')}</strong></article>"
        "</div></section>"
        "<section id=\"editar\" class=\"panel\"><h3>Editar Cliente</h3>"
        f"<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/clients/{escape(client.id)}/update\">"
        f"<label>Nombre<input name=\"display_name\" value=\"{escape(client.display_name)}\" required minlength=\"2\" maxlength=\"150\" /></label>"
        "<label>Tipo cliente<select name=\"client_kind\">"
        f"<option value=\"origin\" {'selected' if client.client_kind.value == 'origin' else ''}>Origen</option>"
        f"<option value=\"destination\" {'selected' if client.client_kind.value == 'destination' else ''}>Destino</option>"
        f"<option value=\"both\" {'selected' if client.client_kind.value == 'both' else ''}>Ambos</option>"
        "</select></label>"
        f"<label>Estado<select id=\"edit-client-state\" name=\"state_code\" required>{state_options}</select></label>"
        f"<label>Municipio<select id=\"edit-client-municipality\" name=\"municipality_code\" required>{municipality_options}</select></label>"
        f"<label>Codigo postal<select id=\"edit-client-postal\" name=\"postal_code\" required>{postal_options}</select></label>"
        f"<label>Colonia<select id=\"edit-client-colony\" name=\"colony_id\" required>{colony_options}</select></label>"
        f"<label>Direccion<input name=\"address_line\" value=\"{escape(client.address_line or '')}\" maxlength=\"255\" /></label>"
        f"<label>Facturar origen<select name=\"wants_invoice\"><option value=\"true\" {'selected' if client.wants_invoice else ''}>Si</option><option value=\"false\" {'selected' if not client.wants_invoice else ''}>No</option></select></label>"
        f"<label>Estado registro<select name=\"active\"><option value=\"true\" {'selected' if client.active else ''}>Activo</option><option value=\"false\" {'selected' if not client.active else ''}>Inactivo</option></select></label>"
        f"<label>Email portal<input type=\"email\" name=\"portal_email\" value=\"{escape(linked_user.email if linked_user else '')}\" /></label>"
        "<label>Password portal (opcional)<input type=\"password\" name=\"portal_password\" minlength=\"8\" /></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Guardar cambios</button><a class=\"btn\" href=\"/ERPMande24/catalogs/clients\">Volver</a></div>"
        "</form></section>"
    )
    content += """
<script>
(() => {
    const stateEl = document.getElementById('edit-client-state');
    const munEl = document.getElementById('edit-client-municipality');
    const postalEl = document.getElementById('edit-client-postal');
    const colonyEl = document.getElementById('edit-client-colony');
    if (!stateEl || !munEl || !postalEl || !colonyEl) return;

    const fill = (el, rows, placeholder, valueKey = 'code', labelKey = 'name') => {
        const current = el.value;
        el.innerHTML = '';
        const first = document.createElement('option');
        first.value = '';
        first.textContent = placeholder;
        el.appendChild(first);
        rows.forEach((row) => {
            const opt = document.createElement('option');
            opt.value = row[valueKey];
            opt.textContent = row[labelKey] || row[valueKey];
            if (opt.value === current) opt.selected = true;
            el.appendChild(opt);
        });
    };

    stateEl.addEventListener('change', async () => {
        const data = await fetch(`/ERPMande24/geo/municipalities?state_code=${encodeURIComponent(stateEl.value)}`).then((r) => r.json());
        fill(munEl, data, 'Selecciona municipio');
        fill(postalEl, [], 'Selecciona municipio');
        fill(colonyEl, [], 'Selecciona codigo postal');
    });

    munEl.addEventListener('change', async () => {
        const data = await fetch(`/ERPMande24/geo/postal-codes?municipality_code=${encodeURIComponent(munEl.value)}`).then((r) => r.json());
        fill(postalEl, data, 'Selecciona codigo postal', 'code', 'code');
        fill(colonyEl, [], 'Selecciona codigo postal');
    });

    postalEl.addEventListener('change', async () => {
        const q = `state_code=${encodeURIComponent(stateEl.value)}&municipality_code=${encodeURIComponent(munEl.value)}&postal_code=${encodeURIComponent(postalEl.value)}`;
        const data = await fetch(`/ERPMande24/geo/colonies?${q}`).then((r) => r.json());
        fill(colonyEl, data, 'Selecciona colonia', 'id', 'name');
    });
})();
</script>
"""
    return _render_layout("clients", f"Cliente {client.display_name}", "Edicion de catalogo de clientes.", content, msg, kind)


@router.post("/catalogs/clients/{client_id}/update")
def backend_update_client(
    client_id: str,
    display_name: str = Form(...),
    client_kind: str = Form("origin"),
    state_code: str = Form(...),
    municipality_code: str = Form(...),
    postal_code: str = Form(...),
    colony_id: str = Form(...),
    address_line: str = Form(""),
    wants_invoice: str = Form("false"),
    active: str = Form("true"),
    portal_email: str = Form(""),
    portal_password: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_ops(request, "/ERPMande24/catalogs/clients", "editar cliente")
    if forbidden:
        return forbidden

    client = db.query(ClientProfile).filter(ClientProfile.id == client_id).first()
    if not client:
        return _redirect("/ERPMande24/catalogs/clients", "Cliente no encontrado.", "error")

    state = db.query(GeoState).filter(GeoState.code == state_code.strip().upper()).first()
    municipality = (
        db.query(GeoMunicipality)
        .filter(GeoMunicipality.code == municipality_code.strip().upper(), GeoMunicipality.state_code == state_code.strip().upper())
        .first()
    )
    postal = (
        db.query(GeoPostalCode)
        .filter(GeoPostalCode.code == postal_code.strip(), GeoPostalCode.municipality_code == municipality_code.strip().upper())
        .first()
    )
    colony = (
        db.query(GeoColony)
        .filter(
            GeoColony.id == colony_id.strip(),
            GeoColony.state_code == state_code.strip().upper(),
            GeoColony.municipality_code == municipality_code.strip().upper(),
            GeoColony.postal_code == postal_code.strip(),
        )
        .first()
    )
    if not state or not municipality or not postal or not colony:
        return _redirect(f"/ERPMande24/catalogs/clients/{client_id}", "Direccion no valida (estado/municipio/CP).", "error")

    try:
        kind_value = ClientKind(client_kind)
    except ValueError:
        return _redirect(f"/ERPMande24/catalogs/clients/{client_id}", "Tipo de cliente no valido.", "error")

    client.display_name = display_name.strip()
    client.client_kind = kind_value
    client.state_code = state.code
    client.municipality_code = municipality.code
    client.postal_code = postal.code
    client.colony_id = colony.id
    client.address_line = address_line.strip()
    client.wants_invoice = wants_invoice == "true"
    client.active = active == "true"

    email_value = portal_email.strip().lower()
    if email_value:
        linked_user = db.query(User).filter(User.id == client.user_id).first() if client.user_id else None
        if linked_user:
            if linked_user.email != email_value and db.query(User).filter(User.email == email_value).first():
                return _redirect(f"/ERPMande24/catalogs/clients/{client_id}", "El email portal ya existe.", "error")
            linked_user.email = email_value
            linked_user.full_name = client.display_name
            if portal_password.strip():
                if len(portal_password.strip()) < 8:
                    return _redirect(f"/ERPMande24/catalogs/clients/{client_id}", "Password portal minimo 8 caracteres.", "error")
                linked_user.password_hash = hash_password(portal_password.strip())
        else:
            if db.query(User).filter(User.email == email_value).first():
                return _redirect(f"/ERPMande24/catalogs/clients/{client_id}", "El email portal ya existe.", "error")
            password_value = portal_password.strip()
            if len(password_value) < 8:
                return _redirect(f"/ERPMande24/catalogs/clients/{client_id}", "Para crear acceso portal captura password minimo 8 caracteres.", "error")
            user = User(
                email=email_value,
                full_name=client.display_name,
                password_hash=hash_password(password_value),
                role=UserRole.client,
                is_active=True,
            )
            db.add(user)
            db.flush()
            client.user_id = user.id

    db.commit()
    return _redirect(f"/ERPMande24/catalogs/clients/{client_id}", "Cliente actualizado correctamente.")


@router.get("/catalogs/pricing-rules", response_class=HTMLResponse)
def backend_pricing_rules(db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    services = db.query(Service).order_by(Service.name.asc()).all()
    stations = db.query(Station).order_by(Station.name.asc()).all()
    rules = db.query(PricingRule).order_by(PricingRule.id.desc()).limit(300).all()

    service_map = {item.id: item for item in services}
    station_map = {item.id: item for item in stations}
    service_options = "".join([f'<option value="{item.id}">{escape(item.name)}</option>' for item in services])
    station_options = "".join([f'<option value="{item.id}">{escape(item.name)}</option>' for item in stations])

    rows = []
    for item in rules:
        service = service_map.get(item.service_id)
        station = station_map.get(item.station_id)
        rows.append(
            [
                f'<input type="checkbox" name="ids" value="{escape(item.id)}" form="bulk-pricing" />',
                escape(item.id),
                escape(service.name if service else item.service_id),
                escape(station.name if station else item.station_id),
                f"{item.price:.2f} {escape(item.currency)}",
                "activa" if item.active else "inactiva",
                (
                    f'<form class="inline-form" method="post" action="/ERPMande24/catalogs/pricing-rules/{escape(item.id)}/toggle">'
                    f'<input type="hidden" name="active" value="{"false" if item.active else "true"}" />'
                    f'<button type="submit">{"Desactivar" if item.active else "Activar"}</button></form>'
                ),
            ]
        )

    form = (
        "<section class=\"panel\"><h3>Nueva Regla de Precio</h3>"
        "<form class=\"grid\" method=\"post\" action=\"/ERPMande24/catalogs/pricing-rules/create\">"
        f"<label>Servicio<select name=\"service_id\" required><option value=\"\">Selecciona</option>{service_options}</select></label>"
        f"<label>Estacion<select name=\"station_id\" required><option value=\"\">Selecciona</option>{station_options}</select></label>"
        "<label>Precio<input name=\"price\" type=\"number\" step=\"0.01\" min=\"0.01\" required /></label>"
        "<label>Moneda<input name=\"currency\" value=\"MXN\" maxlength=\"10\" /></label>"
        "<div class=\"full actions\"><button class=\"primary\" type=\"submit\">Crear Regla</button></div>"
        "</form></section>"
    )

    content = form + f"<section class=\"panel\"><h3>Lista de Tarifas</h3><div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/pricing-rules.csv\">Exportar CSV</a></div>{_bulk_form('bulk-pricing', '/ERPMande24/catalogs/pricing-rules/bulk-toggle', 'Aplicar cambios')}{_table(['Sel', 'ID', 'Servicio', 'Estacion', 'Precio', 'Estado', 'Accion'], rows)}</section>"
    return _render_layout("pricing", "Catalogo de Tarifas", "Reglas de precio por servicio y estacion.", content, msg, kind)


@router.post("/catalogs/pricing-rules/create")
def backend_create_pricing_rule(
    service_id: str = Form(...),
    station_id: str = Form(...),
    price: float = Form(...),
    currency: str = Form("MXN"),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/pricing-rules", "crear tarifa")
    if forbidden:
        return forbidden
    if price <= 0:
        return _redirect("/ERPMande24/catalogs/pricing-rules", "El precio debe ser mayor a cero.", "error")

    if not db.query(Service).filter(Service.id == service_id).first():
        return _redirect("/ERPMande24/catalogs/pricing-rules", "Servicio no encontrado.", "error")

    if not db.query(Station).filter(Station.id == station_id).first():
        return _redirect("/ERPMande24/catalogs/pricing-rules", "Estacion no encontrada.", "error")

    if db.query(PricingRule).filter(PricingRule.service_id == service_id, PricingRule.station_id == station_id).first():
        return _redirect("/ERPMande24/catalogs/pricing-rules", "Ya existe una tarifa para ese servicio y estacion.", "error")

    rule = PricingRule(service_id=service_id, station_id=station_id, price=price, currency=currency.strip().upper(), active=True)
    db.add(rule)
    db.commit()
    return _redirect("/ERPMande24/catalogs/pricing-rules", "Tarifa creada correctamente.")


@router.post("/catalogs/pricing-rules/{rule_id}/toggle")
def backend_toggle_pricing_rule(rule_id: str, active: str = Form(...), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/pricing-rules", "editar tarifa")
    if forbidden:
        return forbidden
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        return _redirect("/ERPMande24/catalogs/pricing-rules", "Regla no encontrada.", "error")
    rule.active = active == "true"
    db.commit()
    return _redirect("/ERPMande24/catalogs/pricing-rules", f"Regla {rule.id} actualizada a {'activa' if rule.active else 'inactiva'}.")


@router.post("/catalogs/pricing-rules/bulk-toggle")
def backend_bulk_toggle_pricing_rules(
    ids: list[str] = Form(default=[]),
    active: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/catalogs/pricing-rules", "editar tarifas")
    if forbidden:
        return forbidden
    if not ids:
        return _redirect("/ERPMande24/catalogs/pricing-rules", "Selecciona al menos una tarifa.", "error")
    value = active == "true"
    updated = db.query(PricingRule).filter(PricingRule.id.in_(ids)).update({PricingRule.active: value}, synchronize_session=False)
    db.commit()
    return _redirect("/ERPMande24/catalogs/pricing-rules", f"Tarifas actualizadas: {updated}.")


@router.get("/users", response_class=HTMLResponse)
def backend_users(
    request: Request,
    db: Session = Depends(get_db),
    q: str = "",
    page: int = 1,
    page_size: int = 25,
    msg: str = "",
    kind: str = "ok",
) -> str:
    safe_page = max(1, page)
    safe_page_size = max(5, min(page_size, 100))
    users_query = db.query(User)
    if q.strip():
        term = f"%{q.strip()}%"
        users_query = users_query.filter(User.full_name.ilike(term) | User.email.ilike(term))

    total = users_query.count()
    offset = (safe_page - 1) * safe_page_size
    users = users_query.order_by(User.created_at.desc()).offset(offset).limit(safe_page_size).all()
    rows = []
    for item in users:
        rows.append(
            [
                f'<input type="checkbox" name="ids" value="{escape(item.id)}" form="bulk-users" />',
                escape(item.id),
                f'<a href="/ERPMande24/users/{escape(item.id)}">{escape(item.full_name)}</a>',
                escape(item.email),
                escape(item.role.value),
                "activo" if item.is_active else "inactivo",
                item.created_at.strftime("%Y-%m-%d %H:%M"),
                (
                    f'<form class="inline-form" method="post" action="/ERPMande24/users/{escape(item.id)}/toggle">'
                    f'<input type="hidden" name="active" value="{"false" if item.is_active else "true"}" />'
                    f'<button type="submit">{"Desactivar" if item.is_active else "Activar"}</button></form>'
                ),
            ]
        )

    pager = _pagination(
        "/ERPMande24/users",
        safe_page,
        safe_page_size,
        total,
        query_params={"q": q.strip()} if q.strip() else None,
    )
    content = (
        f"<section class=\"panel\"><h3>Lista de Usuarios</h3>{_querybox('/ERPMande24/users', 'Buscar por nombre o email', q)}"
        f"{pager}"
        "<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/users.csv\">Exportar CSV</a></div>"
        f"{_bulk_form('bulk-users', '/ERPMande24/users/bulk-toggle', 'Aplicar cambios')}"
        f"{_table(['Sel', 'ID', 'Nombre', 'Email', 'Rol', 'Estado', 'Creado', 'Accion'], rows)}"
        f"{pager}</section>"
    )
    return _render_layout("users", "Usuarios", "Modelo de usuarios del sistema y roles.", content, msg, kind, request=request)


@router.post("/users/{user_id}/toggle")
def backend_toggle_user(user_id: str, active: str = Form(...), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/users", "editar usuario")
    if forbidden:
        return forbidden
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return _redirect("/ERPMande24/users", "Usuario no encontrado.", "error")
    user.is_active = active == "true"
    db.commit()
    return _redirect("/ERPMande24/users", f"Usuario {user.email} actualizado a {'activo' if user.is_active else 'inactivo'}.")


@router.post("/users/bulk-toggle")
def backend_bulk_toggle_users(
    ids: list[str] = Form(default=[]),
    active: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_manage(request, "/ERPMande24/users", "editar usuarios")
    if forbidden:
        return forbidden
    if not ids:
        return _redirect("/ERPMande24/users", "Selecciona al menos un usuario.", "error")
    value = active == "true"
    updated = db.query(User).filter(User.id.in_(ids)).update({User.is_active: value}, synchronize_session=False)
    db.commit()
    return _redirect("/ERPMande24/users", f"Usuarios actualizados: {updated}.")


@router.get("/users/{user_id}", response_class=HTMLResponse)
def backend_user_detail(user_id: str, request: Request, db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return _render_layout("users", "Usuario", "Detalle", '<section class="panel"><div class="empty">Usuario no encontrado.</div></section>', msg, "error", request=request)
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    timeline_events = [(user.created_at.strftime("%Y-%m-%d %H:%M"), "Usuario creado")]
    timeline_events.append((user.created_at.strftime("%Y-%m-%d %H:%M"), f"Rol inicial: {user.role.value}"))
    timeline_events.append((user.created_at.strftime("%Y-%m-%d %H:%M"), f"Estado: {'activo' if user.is_active else 'inactivo'}"))
    if rider:
        timeline_events.append((user.created_at.strftime("%Y-%m-%d %H:%M"), f"Rider vinculado: {rider.id}"))

    content = (
        f"{_tabs([('resumen', 'Resumen'), ('timeline', 'Timeline'), ('operacion', 'Operacion')])}"
        "<section id=\"resumen\" class=\"panel\"><h3>Ficha de Usuario</h3>"
        "<div class=\"kpi-grid\">"
        f"<article class=\"kpi\"><small>ID</small><strong>{escape(user.id)}</strong></article>"
        f"<article class=\"kpi\"><small>Nombre</small><strong>{escape(user.full_name)}</strong></article>"
        f"<article class=\"kpi\"><small>Email</small><strong>{escape(user.email)}</strong></article>"
        f"<article class=\"kpi\"><small>Rol</small><strong>{escape(user.role.value)}</strong></article>"
        f"<article class=\"kpi\"><small>Estado</small><strong>{'activo' if user.is_active else 'inactivo'}</strong></article>"
        f"<article class=\"kpi\"><small>Rider Relacionado</small><strong>{escape(rider.id if rider else 'N/A')}</strong></article>"
        "</div></section>"
        f"<section id=\"timeline\" class=\"panel\"><h3>Timeline</h3>{_timeline(timeline_events)}</section>"
        "<section id=\"operacion\" class=\"panel\"><h3>Operacion</h3><div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/users\">Volver a usuarios</a></div></section>"
    )
    return _render_layout("users", f"Usuario {user.email}", "Vista detalle tipo formulario.", content, msg, kind, request=request)


@router.get("/leads", response_class=HTMLResponse)
def backend_contact_leads(
    request: Request,
    db: Session = Depends(get_db),
    q: str = "",
    status: str = "all",
    page: int = 1,
    page_size: int = 25,
    msg: str = "",
    kind: str = "ok",
) -> str:
    forbidden = _require_ops(request, "/ERPMande24", "consultar leads de contacto")
    if forbidden:
        return _render_layout(
            "dashboard",
            "Sin permisos",
            "No tienes permisos para esta vista.",
            '<section class="panel"><div class="empty">Acceso denegado.</div></section>',
            "Sin permisos para consultar leads.",
            "error",
            request=request,
        )

    allowed_statuses = {"new", "contacted", "closed", "all"}
    safe_status = status if status in allowed_statuses else "all"
    safe_page = max(1, page)
    safe_page_size = max(5, min(page_size, 100))

    query = db.query(ContactLead)
    term = q.strip()
    if term:
        like = f"%{term}%"
        query = query.filter(
            or_(
                ContactLead.full_name.ilike(like),
                ContactLead.company.ilike(like),
                ContactLead.email.ilike(like),
                ContactLead.phone.ilike(like),
                ContactLead.message.ilike(like),
            )
        )
    if safe_status != "all":
        query = query.filter(ContactLead.status == safe_status)

    total = query.count()
    offset = (safe_page - 1) * safe_page_size
    leads = query.order_by(ContactLead.created_at.desc()).offset(offset).limit(safe_page_size).all()

    rows: list[list[str]] = []
    for item in leads:
        rows.append(
            [
                escape(item.id),
                escape(item.full_name),
                escape(item.company or "-"),
                escape(item.email),
                escape(item.phone or "-"),
                escape(item.service_interest),
                escape(item.status),
                escape((item.message or "")[:120] + ("..." if len(item.message or "") > 120 else "")),
                item.created_at.strftime("%Y-%m-%d %H:%M"),
                (
                    f'<form class="inline-form" method="post" action="/ERPMande24/leads/{escape(item.id)}/status">'
                    '<select name="status">'
                    f'<option value="new" {"selected" if item.status == "new" else ""}>new</option>'
                    f'<option value="contacted" {"selected" if item.status == "contacted" else ""}>contacted</option>'
                    f'<option value="closed" {"selected" if item.status == "closed" else ""}>closed</option>'
                    '</select>'
                    '<button type="submit">Guardar</button>'
                    '</form>'
                ),
            ]
        )

    pager_params = {"q": term} if term else {}
    if safe_status != "all":
        pager_params["status"] = safe_status
    pager = _pagination("/ERPMande24/leads", safe_page, safe_page_size, total, query_params=pager_params or None)

    status_filter = (
        '<form class="actions" method="get" action="/ERPMande24/leads">'
        f'<input name="q" value="{escape(term)}" placeholder="Buscar por nombre, email, empresa o mensaje" />'
        '<select name="status">'
        f'<option value="all" {"selected" if safe_status == "all" else ""}>Todos</option>'
        f'<option value="new" {"selected" if safe_status == "new" else ""}>new</option>'
        f'<option value="contacted" {"selected" if safe_status == "contacted" else ""}>contacted</option>'
        f'<option value="closed" {"selected" if safe_status == "closed" else ""}>closed</option>'
        '</select>'
        '<button type="submit">Filtrar</button>'
        '<a class="btn" href="/ERPMande24/leads">Limpiar</a>'
        '</form>'
    )

    content = (
        "<section class=\"panel\"><h3>Leads de Contacto</h3>"
        f"{status_filter}{pager}"
        "<div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/leads.csv\">Exportar CSV</a></div>"
        f"{_table(['ID', 'Nombre', 'Empresa', 'Email', 'Telefono', 'Interes', 'Estado', 'Mensaje', 'Creado', 'Accion'], rows)}"
        f"{pager}</section>"
    )
    return _render_layout("leads", "Leads de Contacto", "Seguimiento comercial de solicitudes web.", content, msg, kind, request=request)


@router.post("/leads/{lead_id}/status")
def backend_update_contact_lead_status(
    lead_id: str,
    status: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    forbidden = _require_ops(request, "/ERPMande24/leads", "actualizar estado de lead")
    if forbidden:
        return forbidden

    safe_status = status.strip().lower()
    if safe_status not in {"new", "contacted", "closed"}:
        return _redirect("/ERPMande24/leads", "Estado de lead no valido.", "error")

    lead = db.query(ContactLead).filter(ContactLead.id == lead_id).first()
    if not lead:
        return _redirect("/ERPMande24/leads", "Lead no encontrado.", "error")

    lead.status = safe_status
    db.commit()
    return _redirect("/ERPMande24/leads", f"Lead {lead.email} actualizado a {safe_status}.")


@router.get("/commissions/riders", response_class=HTMLResponse)
def backend_rider_commissions(db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    rows_db = db.query(RiderCommission).order_by(RiderCommission.week_start.desc()).limit(200).all()
    rows = [
        [
            escape(item.id),
            escape(item.rider_id),
            item.week_start.isoformat(),
            str(item.delivery_count),
            f"{item.total_amount:.2f}",
            escape(item.state),
        ]
        for item in rows_db
    ]
    close_form = (
        "<section class=\"panel\"><h3>Cierre Semanal Riders</h3>"
        "<form class=\"actions\" method=\"post\" action=\"/ERPMande24/commissions/riders/close\" data-confirm=\"Se ejecutara el cierre semanal de comisiones rider. Continuar?\">"
        "<input name=\"week_start\" placeholder=\"YYYY-MM-DD (opcional)\" />"
        "<button class=\"primary\" type=\"submit\">Cerrar Semana Riders</button>"
        "</form></section>"
    )
    content = close_form + f"<section class=\"panel\"><h3>Historico Comisiones Rider</h3><div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/commissions-riders.csv\">Exportar CSV</a></div>{_table(['ID', 'Rider ID', 'Week Start', 'Entregas', 'Total', 'Estado'], rows)}</section>"
    return _render_layout("comm_rider", "Comisiones Rider", "Snapshots semanales de comision por rider.", content, msg, kind)


@router.get("/commissions/stations", response_class=HTMLResponse)
def backend_station_commissions(db: Session = Depends(get_db), msg: str = "", kind: str = "ok") -> str:
    rows_db = db.query(StationCommission).order_by(StationCommission.week_start.desc()).limit(200).all()
    rows = [
        [
            escape(item.id),
            escape(item.station_id),
            item.week_start.isoformat(),
            str(item.sold_guide_count),
            f"{item.sold_guide_amount:.2f}",
            f"{item.total_amount:.2f}",
            escape(item.state),
        ]
        for item in rows_db
    ]
    close_form = (
        "<section class=\"panel\"><h3>Cierre Semanal Estaciones</h3>"
        "<form class=\"actions\" method=\"post\" action=\"/ERPMande24/commissions/stations/close\" data-confirm=\"Se ejecutara el cierre semanal de comisiones estacion. Continuar?\">"
        "<input name=\"week_start\" placeholder=\"YYYY-MM-DD (opcional)\" />"
        "<button class=\"primary\" type=\"submit\">Cerrar Semana Estaciones</button>"
        "</form></section>"
    )
    content = close_form + f"<section class=\"panel\"><h3>Historico Comisiones Estacion</h3><div class=\"actions\"><a class=\"btn\" href=\"/ERPMande24/export/commissions-stations.csv\">Exportar CSV</a></div>{_table(['ID', 'Station ID', 'Week Start', 'Guias', 'Venta', 'Total', 'Estado'], rows)}</section>"
    return _render_layout("comm_station", "Comisiones Estacion", "Snapshots semanales de comision por estacion.", content, msg, kind)


@router.post("/commissions/riders/close")
def backend_close_rider_commissions(week_start: str = Form(""), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_ops(request, "/ERPMande24/commissions/riders", "cerrar comisiones rider")
    if forbidden:
        return forbidden
    try:
        start_dt, end_dt, monday = resolve_week_window(week_start.strip() or None)
        rows = close_rider_week(db, monday, start_dt, end_dt)
        return _redirect("/ERPMande24/commissions/riders", f"Cierre rider ejecutado: {len(rows)} registros.")
    except Exception as exc:
        return _redirect("/ERPMande24/commissions/riders", f"Error en cierre rider: {exc}", "error")


@router.post("/commissions/stations/close")
def backend_close_station_commissions(week_start: str = Form(""), request: Request = None, db: Session = Depends(get_db)) -> RedirectResponse:
    forbidden = _require_ops(request, "/ERPMande24/commissions/stations", "cerrar comisiones estacion")
    if forbidden:
        return forbidden
    try:
        start_dt, end_dt, monday = resolve_week_window(week_start.strip() or None)
        rows = close_station_week(db, monday, start_dt, end_dt)
        return _redirect("/ERPMande24/commissions/stations", f"Cierre estacion ejecutado: {len(rows)} registros.")
    except Exception as exc:
        return _redirect("/ERPMande24/commissions/stations", f"Error en cierre estacion: {exc}", "error")


@router.post("/demo/seed")
def backend_seed_demo_data(db: Session = Depends(get_db)) -> JSONResponse:
    data = _seed_demo_data(db)
    return JSONResponse(status_code=200, content=data)


@router.post("/demo/seed/form")
def backend_seed_demo_data_form(db: Session = Depends(get_db)) -> RedirectResponse:
    _seed_demo_data(db)
    return _redirect("/ERPMande24/guides/new", "Datos demo creados correctamente.")


@router.get("/export/guides.csv")
def backend_export_guides_csv(db: Session = Depends(get_db)) -> Response:
    guides = db.query(Guide).order_by(Guide.created_at.desc()).limit(2000).all()
    rows = [
        [
            item.guide_code,
            item.customer_name,
            item.destination_name,
            item.service_type,
            f"{item.sale_amount:.2f}",
            item.currency,
            item.created_at.isoformat(),
        ]
        for item in guides
    ]
    return _csv_response("guides.csv", ["guide_code", "customer_name", "destination_name", "service_type", "sale_amount", "currency", "created_at"], rows)


@router.get("/export/deliveries.csv")
def backend_export_deliveries_csv(db: Session = Depends(get_db)) -> Response:
    deliveries = db.query(Delivery).order_by(Delivery.updated_at.desc()).limit(3000).all()
    rows = [
        [
            item.id,
            item.guide.guide_code if item.guide else "",
            item.stage.value,
            str(item.has_evidence),
            str(item.has_signature),
            item.updated_at.isoformat(),
        ]
        for item in deliveries
    ]
    return _csv_response("deliveries.csv", ["delivery_id", "guide_code", "stage", "has_evidence", "has_signature", "updated_at"], rows)


@router.get("/export/services.csv")
def backend_export_services_csv(db: Session = Depends(get_db)) -> Response:
    services = db.query(Service).order_by(Service.name.asc()).all()
    rows = [[item.id, item.name, item.service_type.value, str(item.active), item.description or ""] for item in services]
    return _csv_response("services.csv", ["id", "name", "service_type", "active", "description"], rows)


@router.get("/export/zones.csv")
def backend_export_zones_csv(db: Session = Depends(get_db)) -> Response:
    zones = db.query(Zone).order_by(Zone.name.asc()).all()
    rows = [[item.id, item.name, item.code, str(item.active)] for item in zones]
    return _csv_response("zones.csv", ["id", "name", "code", "active"], rows)


@router.get("/export/stations.csv")
def backend_export_stations_csv(db: Session = Depends(get_db)) -> Response:
    stations = db.query(Station).order_by(Station.name.asc()).all()
    rows = [[item.id, item.name, item.zone_id, str(item.active)] for item in stations]
    return _csv_response("stations.csv", ["id", "name", "zone_id", "active"], rows)


@router.get("/export/riders.csv")
def backend_export_riders_csv(db: Session = Depends(get_db)) -> Response:
    riders = db.query(Rider).order_by(Rider.id.desc()).all()
    rows = [[item.id, item.user_id, item.zone_id or "", item.vehicle_type, item.state.value, str(item.active)] for item in riders]
    return _csv_response("riders.csv", ["id", "user_id", "zone_id", "vehicle_type", "state", "active"], rows)


@router.get("/export/pricing-rules.csv")
def backend_export_pricing_rules_csv(db: Session = Depends(get_db)) -> Response:
    rules = db.query(PricingRule).order_by(PricingRule.id.desc()).all()
    rows = [[item.id, item.service_id, item.station_id, f"{item.price:.2f}", item.currency, str(item.active)] for item in rules]
    return _csv_response("pricing_rules.csv", ["id", "service_id", "station_id", "price", "currency", "active"], rows)


@router.get("/export/users.csv")
def backend_export_users_csv(db: Session = Depends(get_db)) -> Response:
    users = db.query(User).order_by(User.created_at.desc()).all()
    rows = [[item.id, item.full_name, item.email, item.role.value, str(item.is_active), item.created_at.isoformat()] for item in users]
    return _csv_response("users.csv", ["id", "full_name", "email", "role", "is_active", "created_at"], rows)


@router.get("/export/leads.csv")
def backend_export_leads_csv(db: Session = Depends(get_db)) -> Response:
    leads = db.query(ContactLead).order_by(ContactLead.created_at.desc()).limit(3000).all()
    rows = [
        [
            item.id,
            item.full_name,
            item.company or "",
            item.email,
            item.phone or "",
            item.service_interest,
            item.status,
            item.message,
            item.created_at.isoformat(),
            item.updated_at.isoformat() if item.updated_at else "",
        ]
        for item in leads
    ]
    return _csv_response(
        "leads.csv",
        ["id", "full_name", "company", "email", "phone", "service_interest", "status", "message", "created_at", "updated_at"],
        rows,
    )


@router.get("/export/clients.csv")
def backend_export_clients_csv(
    db: Session = Depends(get_db),
    q: str = "",
    client_kind: str = "",
    state_code: str = "",
) -> Response:
    clients_query = db.query(ClientProfile)
    if client_kind in {"origin", "destination", "both"}:
        if client_kind == "origin":
            clients_query = clients_query.filter(ClientProfile.client_kind.in_([ClientKind.origin, ClientKind.both]))
        elif client_kind == "destination":
            clients_query = clients_query.filter(ClientProfile.client_kind.in_([ClientKind.destination, ClientKind.both]))
        else:
            clients_query = clients_query.filter(ClientProfile.client_kind == ClientKind.both)

    if state_code.strip():
        clients_query = clients_query.filter(ClientProfile.state_code == state_code.strip().upper())

    if q.strip():
        term = f"%{q.strip()}%"
        clients_query = clients_query.filter(
            ClientProfile.display_name.ilike(term)
            | ClientProfile.state_code.ilike(term)
            | ClientProfile.municipality_code.ilike(term)
            | ClientProfile.postal_code.ilike(term)
        )

    clients = clients_query.order_by(ClientProfile.created_at.desc()).all()
    states = {item.code: item for item in db.query(GeoState).all()}
    municipalities = {item.code: item for item in db.query(GeoMunicipality).all()}
    colony_ids = [item.colony_id for item in clients if item.colony_id]
    colonies = {}
    if colony_ids:
        colonies = {item.id: item for item in db.query(GeoColony).filter(GeoColony.id.in_(colony_ids)).all()}
    rows = []
    for item in clients:
        state = states.get(item.state_code)
        municipality = municipalities.get(item.municipality_code)
        colony = colonies.get(item.colony_id) if item.colony_id else None
        rows.append(
            [
                item.id,
                item.display_name,
                item.client_kind.value,
                state.name if state else item.state_code,
                municipality.name if municipality else item.municipality_code,
                item.postal_code,
                colony.name if colony else "",
                item.address_line or "",
                str(item.wants_invoice),
                item.user_id or "",
                str(item.active),
                item.created_at.isoformat(),
            ]
        )
    return _csv_response(
        "clients.csv",
        [
            "id",
            "display_name",
            "client_kind",
            "state",
            "municipality",
            "postal_code",
            "colony",
            "address_line",
            "wants_invoice",
            "user_id",
            "active",
            "created_at",
        ],
        rows,
    )


@router.get("/export/commissions-riders.csv")
def backend_export_commissions_riders_csv(db: Session = Depends(get_db)) -> Response:
    items = db.query(RiderCommission).order_by(RiderCommission.week_start.desc()).all()
    rows = [[item.id, item.rider_id, item.week_start.isoformat(), item.delivery_count, f"{item.total_amount:.2f}", item.state] for item in items]
    return _csv_response("commissions_riders.csv", ["id", "rider_id", "week_start", "delivery_count", "total_amount", "state"], rows)


@router.get("/export/commissions-stations.csv")
def backend_export_commissions_stations_csv(db: Session = Depends(get_db)) -> Response:
    items = db.query(StationCommission).order_by(StationCommission.week_start.desc()).all()
    rows = [[item.id, item.station_id, item.week_start.isoformat(), item.sold_guide_count, f"{item.sold_guide_amount:.2f}", f"{item.total_amount:.2f}", item.state] for item in items]
    return _csv_response("commissions_stations.csv", ["id", "station_id", "week_start", "sold_guide_count", "sold_guide_amount", "total_amount", "state"], rows)

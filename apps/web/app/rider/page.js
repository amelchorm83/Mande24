"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ROUTE_LABELS = {
  pickup_to_origin_station: "Recoleccion a estacion origen",
  station_to_station: "Estacion a estacion",
  destination_station_to_client: "Estacion destino a cliente",
  pickup_to_station: "Recoleccion a estacion",
  station_to_client: "Estacion a cliente",
  pickup_to_client: "Recoleccion a cliente",
};

const STATUS_LABELS = {
  assigned: "Asignado",
  picked_up: "Recolectado",
  in_transit: "En transito",
  at_station: "En estacion",
  out_for_delivery: "En ruta de entrega",
  delivered: "Entregado",
  in_progress: "En progreso",
  completed: "Completado",
  failed: "Fallido",
};

function formatRouteType(value) {
  return ROUTE_LABELS[value] || String(value || "-").replaceAll("_", " ");
}

function formatStatus(value) {
  return STATUS_LABELS[value] || String(value || "-").replaceAll("_", " ");
}

export default function RiderPortalPage() {
  const [section, setSection] = useState("actualizar");
  const [token, setToken] = useState("");
  const [currentUserName, setCurrentUserName] = useState("");
  const [currentUserEmail, setCurrentUserEmail] = useState("");
  const [deliveryId, setDeliveryId] = useState("");
  const [routeGuideCode, setRouteGuideCode] = useState("");
  const [routeLegRows, setRouteLegRows] = useState([]);
  const [myRouteLegRows, setMyRouteLegRows] = useState([]);
  const [selectedRouteLegId, setSelectedRouteLegId] = useState("");
  const [routeStatus, setRouteStatus] = useState("in_progress");
  const [stage, setStage] = useState("in_transit");
  const [hasEvidence, setHasEvidence] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem("m24_token") || "");
    setCurrentUserName(localStorage.getItem("m24_full_name") || "");
    setCurrentUserEmail(localStorage.getItem("m24_email") || "");
  }, []);

  useEffect(() => {
    if (!token || token.split(".").length !== 3) {
      return;
    }
    loadCurrentUser();
  }, [token]);

  async function loadCurrentUser() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const safeName = data.full_name || "";
      const safeEmail = data.email || "";
      setCurrentUserName(safeName);
      setCurrentUserEmail(safeEmail);
      if (safeName) localStorage.setItem("m24_full_name", safeName);
      if (safeEmail) localStorage.setItem("m24_email", safeEmail);
    } catch {
      // Mantiene el portal operativo aunque no se pueda resolver el perfil.
    }
  }

  async function updateStage(e) {
    e.preventDefault();
    if (!deliveryId) {
      setMsg("Ingresa delivery_id");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/guides/deliveries/${deliveryId}/stage`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ stage, has_evidence: hasEvidence, has_signature: hasSignature }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error: ${JSON.stringify(data)}`);
        return;
      }
      setMsg(`Entrega actualizada: ${formatStatus(data.stage)}`);
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

  async function loadMyRouteLegs() {
    if (!token) {
      setMsg("Necesitas token para consultar tramos.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/guides/route-legs/my`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error cargando tramos: ${JSON.stringify(data)}`);
        return;
      }
      setMyRouteLegRows(data);
      setMsg(`Tramos asignados cargados: ${data.length}`);
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

  async function loadGuideRouteLegs() {
    if (!token || !routeGuideCode) {
      setMsg("Captura guía y token para consultar ruta.");
      return;
    }
    try {
      const code = encodeURIComponent(routeGuideCode.trim().toUpperCase());
      const res = await fetch(`${API_BASE}/api/v1/guides/${code}/route-legs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error ruta: ${JSON.stringify(data)}`);
        return;
      }
      setRouteLegRows(data);
      setSelectedRouteLegId(data.length ? data[0].id : "");
      setMsg(`Ruta cargada: ${data.length} tramos.`);
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

  async function updateRouteLegStatus(e) {
    e.preventDefault();
    if (!token || !selectedRouteLegId) {
      setMsg("Selecciona un tramo y token valido.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/guides/route-legs/${selectedRouteLegId}/assign`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ status: routeStatus }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error tramo: ${JSON.stringify(data)}`);
        return;
      }
      setMsg(`Tramo ${data.sequence} actualizado a ${formatStatus(data.status)}`);
      await loadGuideRouteLegs();
      await loadMyRouteLegs();
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <img className="brand-logo" src="/brand/icon.svg" alt="Icono Mande24" />
          <div className="brand-copy">
            <h2>Portal Repartidor</h2>
            <p className="brand-slogan">Seguimiento de entrega en tiempo real.</p>
          </div>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/auth">Portal Acceso</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link active" href="/rider">Portal Repartidor</a>
          <a className="nav-link" href="/station">Portal Estación</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Portal Repartidor</span>
      <h1>Control de Entrega en Ruta</h1>
      <p className="hero-note">Captura el <code>delivery_id</code> generado en Cliente y actualiza la entrega por etapas. Para <code>delivered</code> se requiere evidencia y firma.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner portal repartidor" />

      <section className="panel session-card">
        <div className="session-grid">
          <div>
            <span className="badge">Sesión y PWA</span>
            <h3>Usuario visible en todos los módulos</h3>
            <p className="field-hint">La identidad del repartidor permanece visible mientras actualiza etapas, revisa rutas y ejecuta tramos asignados.</p>
          </div>
          <div className="card session-summary">
            <p><strong>Usuario:</strong> {currentUserName || "Sin identificar"}</p>
            <p><strong>Email:</strong> {currentUserEmail || "Sin email cargado"}</p>
            <p><strong>Estado:</strong> {token ? "Sesión con token disponible" : "Sin token activo"}</p>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-rider.svg" alt="Repartidor en ruta con control de etapas" />
            <div>
              <h3>Operación de Ruta</h3>
              <p className="hero-note">Actualiza etapas, evidencia y firma para cerrar entregas con trazabilidad completa.</p>
            </div>
          </article>
        </div>
      </section>

      <nav className="section-nav">
        <button className={section === "actualizar" ? "section-link active" : "section-link"} onClick={() => setSection("actualizar")}>Actualizar Etapa</button>
        <button className={section === "rutas" ? "section-link active" : "section-link"} onClick={() => setSection("rutas")}>Rutas Asignadas</button>
        <button className={section === "guia" ? "section-link active" : "section-link"} onClick={() => setSection("guia")}>Guía Rápida</button>
      </nav>

      {section === "actualizar" && <section className="panel">
        <h2>Actualización de Etapa</h2>
        <form className="form-grid" onSubmit={updateStage}>
          <label>
            Token de acceso (Bearer)
            <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
          </label>
          <label>
            ID de entrega
            <input value={deliveryId} onChange={(e) => setDeliveryId(e.target.value)} required />
          </label>
          <label>
            Nueva etapa
            <select value={stage} onChange={(e) => setStage(e.target.value)}>
              <option value="assigned">Asignado</option>
              <option value="picked_up">Recolectado</option>
              <option value="in_transit">En tránsito</option>
              <option value="at_station">En estación</option>
              <option value="out_for_delivery">En ruta de entrega</option>
              <option value="delivered">Entregado</option>
              <option value="failed">No entregado</option>
            </select>
          </label>
          <label className="check-row">
            <input type="checkbox" checked={hasEvidence} onChange={(e) => setHasEvidence(e.target.checked)} />
            Evidencia
          </label>
          <label className="check-row">
            <input type="checkbox" checked={hasSignature} onChange={(e) => setHasSignature(e.target.checked)} />
            Firma
          </label>
          <button className="btn btn-primary" type="submit">Actualizar etapa</button>
        </form>
        <p className={`status-line ${msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
      </section>}

      {section === "rutas" && <section className="panel">
        <h2>Ejecución de Tramos de Ruta</h2>
        <div className="form-grid">
          <label>
            Token de acceso (Bearer)
            <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
          </label>
          <label>
            Código de guía
            <input value={routeGuideCode} onChange={(e) => setRouteGuideCode(e.target.value)} placeholder="M24-20260310-XXXXXX" />
          </label>
        </div>
        <div className="inline-actions">
          <button className="btn btn-ghost" type="button" onClick={loadMyRouteLegs}>Ver mis tramos</button>
          <button className="btn" type="button" onClick={loadGuideRouteLegs}>Cargar ruta de guía</button>
        </div>

        <form className="form-grid" onSubmit={updateRouteLegStatus}>
          <label>
            Tramo
            <select value={selectedRouteLegId} onChange={(e) => setSelectedRouteLegId(e.target.value)}>
              <option value="">Selecciona tramo</option>
              {routeLegRows.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.sequence} {formatRouteType(item.leg_type)} | {formatStatus(item.status)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Nuevo estado de tramo
            <select value={routeStatus} onChange={(e) => setRouteStatus(e.target.value)}>
              <option value="in_progress">En progreso</option>
              <option value="completed">Completado</option>
              <option value="failed">Fallido</option>
            </select>
          </label>
          <button className="btn btn-primary" type="submit">Actualizar tramo</button>
        </form>

        <h3>Tramos de la guía</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Secuencia</th><th>Tipo</th><th>Estado</th><th>Repartidor</th><th>Est. origen</th><th>Est. destino</th></tr></thead>
            <tbody>
              {routeLegRows.map((item) => (
                <tr key={item.id}>
                  <td>{item.sequence}</td><td>{formatRouteType(item.leg_type)}</td><td>{formatStatus(item.status)}</td><td>{item.assigned_rider_id || "-"}</td><td>{item.origin_station_id || "-"}</td><td>{item.destination_station_id || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3>Mis tramos asignados</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Guía</th><th>Seq</th><th>Tipo</th><th>Estado</th><th>Actualizado</th></tr></thead>
            <tbody>
              {myRouteLegRows.map((item) => (
                <tr key={item.id}><td>{item.guide_code}</td><td>{item.sequence}</td><td>{formatRouteType(item.leg_type)}</td><td>{formatStatus(item.status)}</td><td>{new Date(item.updated_at).toLocaleString()}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className={`status-line ${msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
      </section>}

      {section === "guia" && <section className="panel">
        <h2>Guía Operativa de Etapas</h2>
        <ol className="flow-list">
          <li><code>assigned</code>: pedido asignado al repartidor.</li>
          <li><code>picked_up</code> y <code>in_transit</code>: envío en traslado.</li>
          <li><code>delivered</code>: registrar <code>Evidencia</code> y <code>Firma</code> para validar cierre.</li>
        </ol>
      </section>}
    </main>
  );
}

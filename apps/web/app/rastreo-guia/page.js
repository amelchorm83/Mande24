"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function formatStage(stage) {
  if (!stage) return "Sin estado";
  const labels = {
    assigned: "Asignado",
    picked_up: "Recolectado",
    in_transit: "En transito",
    at_station: "En estacion",
    out_for_delivery: "En ruta de entrega",
    delivered: "Entregado",
    failed: "Fallido",
  };
  return labels[stage] || stage.replaceAll("_", " ");
}

export default function RastreoGuiaPage() {
  const [guideCode, setGuideCode] = useState("");
  const [tracking, setTracking] = useState(null);
  const [statusMsg, setStatusMsg] = useState("Ingresa un folio para consultar.");
  const [isLoading, setIsLoading] = useState(false);

  async function onSearch() {
    const normalized = guideCode.trim().toUpperCase();
    if (!normalized) {
      setStatusMsg("Ingresa un folio válido.");
      setTracking(null);
      return;
    }

    setIsLoading(true);
    setStatusMsg("Consultando rastreo...");
    try {
      const res = await fetch(`${API_BASE}/api/v1/public/tracking/${encodeURIComponent(normalized)}`);
      const data = await res.json();
      if (!res.ok) {
        setTracking(null);
        setStatusMsg(data?.detail || "No se encontró información para este folio.");
        return;
      }
      setTracking(data);
      setStatusMsg("Estado actualizado desde API.");
    } catch (error) {
      setTracking(null);
      setStatusMsg(`Error de red: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="shell public-shell">
      <header className="topbar">
        <div className="brand">
          <img className="brand-logo" src="/brand/icon.svg" alt="Icono Mande24" />
          <div className="brand-copy">
            <h2>Mande24 Logistics</h2>
            <p className="brand-slogan">Entrega segura. Ruta inteligente.</p>
          </div>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/centro-ayuda">Centro de Ayuda</a>
          <a className="nav-link active" href="/rastreo-guia">Rastreo</a>
        </nav>
      </header>

      <span className="badge">Rastreo de Guía</span>
      <h1>Consulta el estado de tu envío con tu folio.</h1>
      <p className="hero-note">Consulta pública conectada a la API de Mande24 para validar etapa actual y datos clave del envío.</p>

      <section className="panel contact-grid">
        <article className="card">
          <h2>Buscar folio</h2>
          <label>
            Folio de guía
            <input
              value={guideCode}
              onChange={(e) => setGuideCode(e.target.value)}
              placeholder="Ejemplo: M24-20260309-ABC123"
            />
          </label>
          <div className="inline-actions">
            <button className="btn btn-primary" type="button" disabled={isLoading} onClick={onSearch}>{isLoading ? "Consultando..." : "Buscar guía"}</button>
          </div>
          <p className={`status-line ${statusMsg.includes("Error") || statusMsg.includes("No se") ? "warn" : "ok"}`}>{statusMsg}</p>
        </article>

        <article className="card">
          <h2>Estado</h2>
          <p className="kpi"><strong>{tracking ? formatStage(tracking.stage) : "Sin consulta"}</strong></p>
          <p className="field-hint">Folio: {tracking?.guide_code || "--"}</p>
          <p className="field-hint">Cliente origen: {tracking?.customer_name || "--"}</p>
          <p className="field-hint">Destino: {tracking?.destination_name || "--"}</p>
          <p className="field-hint">Última actualización: {tracking?.updated_at ? new Date(tracking.updated_at).toLocaleString() : "--"}</p>
          <p className="field-hint">Evidencia: {tracking ? (tracking.has_evidence ? "Sí" : "No") : "--"}</p>
          <p className="field-hint">Firma: {tracking ? (tracking.has_signature ? "Sí" : "No") : "--"}</p>
          <div className="inline-actions">
            <a className="btn" href="/contacto">Reportar incidencia</a>
            <a className="btn btn-primary" href="/auth">Ingresar al portal</a>
          </div>
        </article>
      </section>
    </main>
  );
}

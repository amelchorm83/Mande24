"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CotizadorPage() {
  const [distanceKm, setDistanceKm] = useState(8);
  const [stops, setStops] = useState(1);
  const [zoneType, setZoneType] = useState("urbana");
  const [ruralComplexity, setRuralComplexity] = useState("media");
  const [serviceType, setServiceType] = useState("programado");
  const [estimate, setEstimate] = useState(null);
  const [statusMsg, setStatusMsg] = useState("Calculando cotización...");
  const [isLoading, setIsLoading] = useState(false);

  async function fetchQuote() {
    setIsLoading(true);
    setStatusMsg("Calculando cotización...");
    try {
      const res = await fetch(`${API_BASE}/api/v1/public/quote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          distance_km: Number(distanceKm),
          stops: Number(stops),
          zone_type: zoneType,
          rural_complexity: ruralComplexity,
          service_type: serviceType,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setEstimate(null);
        setStatusMsg(`No se pudo calcular: ${JSON.stringify(data)}`);
        return;
      }
      setEstimate(data);
      setStatusMsg(data.message || "Cotización calculada.");
    } catch (error) {
      setEstimate(null);
      setStatusMsg(`Error de red: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchQuote();
    // Recalculate automatically when quote parameters change.
  }, [distanceKm, stops, zoneType, serviceType, ruralComplexity]);

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
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link active" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a>
        </nav>
      </header>

      <span className="badge">Cotizador Express</span>
      <h1>Estima tu envío en segundos para el sureste: Tabasco, Campeche, Chiapas, Yucatán y Quintana Roo.</h1>
      <p className="hero-note">Este cotizador es referencial y ayuda a comparar escenarios por distancia, tipo de zona y nivel de urgencia.</p>

      <section className="panel contact-grid">
        <article className="card">
          <h2>Parámetros del servicio</h2>
          <form className="form-grid">
            <label>
              Distancia estimada (km)
              <input
                type="number"
                min={1}
                max={120}
                value={distanceKm}
                onChange={(e) => setDistanceKm(Number(e.target.value || 1))}
              />
            </label>
            <label>
              Número de paradas
              <input
                type="number"
                min={1}
                max={8}
                value={stops}
                onChange={(e) => setStops(Number(e.target.value || 1))}
              />
            </label>
            <label>
              Tipo de zona
              <select value={zoneType} onChange={(e) => setZoneType(e.target.value)}>
                <option value="urbana">Urbana</option>
                <option value="metropolitana">Metropolitana</option>
                <option value="intermunicipal">Intermunicipal</option>
                <option value="rural">Rural</option>
              </select>
            </label>
            <label>
              Complejidad rural
              <select value={ruralComplexity} onChange={(e) => setRuralComplexity(e.target.value)}>
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
              </select>
            </label>
            <label>
              Tipo de servicio
              <select value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
                <option value="programado">Programado</option>
                <option value="express">Exprés</option>
                <option value="recurrente">Recurrente</option>
                <option value="mandaditos">Mandaditos</option>
                <option value="paqueteria">Paquetería</option>
              </select>
            </label>
          </form>
        </article>

        <article className="card">
          <h2>Resultado estimado</h2>
          <p className="kpi">Total aproximado: <strong>{estimate ? `$${estimate.total_estimate} ${estimate.currency}` : "--"}</strong></p>
          <p className="kpi">Tiempo estimado: <strong>{estimate ? `${estimate.eta_minutes} min` : "--"}</strong></p>
          {estimate && (
            <p className="hero-note">
              Tipo solicitado: <strong>{estimate.requested_service_type}</strong> | Tipo aplicado: <strong>{estimate.applied_service_type}</strong>
            </p>
          )}
          {estimate?.service_converted && (
            <p className="status-line warn">
              Mandaditos se convirtio a paqueteria por superar 10 km de distancia.
            </p>
          )}
          {Array.isArray(estimate?.policy_notes) && estimate.policy_notes.length > 0 && (
            <ul className="flow-list">
              {estimate.policy_notes.map((note, idx) => (
                <li key={`policy-note-${idx}`}>{note}</li>
              ))}
            </ul>
          )}
          <p className={`status-line ${statusMsg.includes("Error") || statusMsg.includes("No se pudo") ? "warn" : "ok"}`}>{statusMsg}</p>
          <button className="btn" type="button" disabled={isLoading} onClick={fetchQuote}>{isLoading ? "Calculando..." : "Recalcular"}</button>
          <p className="field-hint">El precio final puede variar por horario, saturación operativa, dimensiones del paquete y políticas vigentes.</p>
          <div className="inline-actions">
            <a className="btn btn-primary" href="/contacto">Solicitar propuesta formal</a>
            <a className="btn" href="/niveles-servicio">Ver niveles de servicio</a>
          </div>
        </article>
      </section>
    </main>
  );
}

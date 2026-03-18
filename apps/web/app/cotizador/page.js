"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MX_STATES = [
  { code: "AGU", name: "Aguascalientes" },
  { code: "BCN", name: "Baja California" },
  { code: "BCS", name: "Baja California Sur" },
  { code: "CAM", name: "Campeche" },
  { code: "CHP", name: "Chiapas" },
  { code: "CHH", name: "Chihuahua" },
  { code: "CMX", name: "Ciudad de Mexico" },
  { code: "COA", name: "Coahuila" },
  { code: "COL", name: "Colima" },
  { code: "DUR", name: "Durango" },
  { code: "GUA", name: "Guanajuato" },
  { code: "GRO", name: "Guerrero" },
  { code: "HID", name: "Hidalgo" },
  { code: "JAL", name: "Jalisco" },
  { code: "MEX", name: "Estado de Mexico" },
  { code: "MIC", name: "Michoacan" },
  { code: "MOR", name: "Morelos" },
  { code: "NAY", name: "Nayarit" },
  { code: "NLE", name: "Nuevo Leon" },
  { code: "OAX", name: "Oaxaca" },
  { code: "PUE", name: "Puebla" },
  { code: "QUE", name: "Queretaro" },
  { code: "ROO", name: "Quintana Roo" },
  { code: "SLP", name: "San Luis Potosi" },
  { code: "SIN", name: "Sinaloa" },
  { code: "SON", name: "Sonora" },
  { code: "TAB", name: "Tabasco" },
  { code: "TAM", name: "Tamaulipas" },
  { code: "TLA", name: "Tlaxcala" },
  { code: "VER", name: "Veracruz" },
  { code: "YUC", name: "Yucatan" },
  { code: "ZAC", name: "Zacatecas" },
];

export default function CotizadorPage() {
  const [distanceKm, setDistanceKm] = useState(8);
  const [stops, setStops] = useState(1);
  const [zoneType, setZoneType] = useState("urbana");
  const [ruralComplexity, setRuralComplexity] = useState("media");
  const [serviceType, setServiceType] = useState("programado");
  const [originStateCode, setOriginStateCode] = useState("CMX");
  const [destinationStateCode, setDestinationStateCode] = useState("MEX");
  const [originZoneCode, setOriginZoneCode] = useState("URB-CENTRO");
  const [destinationZoneCode, setDestinationZoneCode] = useState("URB-NORTE");
  const [useStationHandoff, setUseStationHandoff] = useState(false);
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
          origin_state_code: originStateCode,
          destination_state_code: destinationStateCode,
          origin_zone_code: originZoneCode,
          destination_zone_code: destinationZoneCode,
          use_station_handoff: useStationHandoff,
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
  }, [distanceKm, stops, zoneType, serviceType, ruralComplexity, originStateCode, destinationStateCode, originZoneCode, destinationZoneCode, useStationHandoff]);

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
      <h1>Estima tu envío a nivel nacional en toda la Republica Mexicana.</h1>
      <p className="hero-note">Cotizador referencial para escenarios interestatales por region, zona y transferencia entre estaciones de servicio.</p>

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
              Estado origen
              <select value={originStateCode} onChange={(e) => setOriginStateCode(e.target.value)}>
                {MX_STATES.map((state) => (
                  <option key={`origin-${state.code}`} value={state.code}>{state.name}</option>
                ))}
              </select>
            </label>
            <label>
              Estado destino
              <select value={destinationStateCode} onChange={(e) => setDestinationStateCode(e.target.value)}>
                {MX_STATES.map((state) => (
                  <option key={`destination-${state.code}`} value={state.code}>{state.name}</option>
                ))}
              </select>
            </label>
            <label>
              Zona operativa origen
              <input
                type="text"
                value={originZoneCode}
                onChange={(e) => setOriginZoneCode(e.target.value.toUpperCase())}
              />
            </label>
            <label>
              Zona operativa destino
              <input
                type="text"
                value={destinationZoneCode}
                onChange={(e) => setDestinationZoneCode(e.target.value.toUpperCase())}
              />
            </label>
            <label className="check-row">
              <input
                type="checkbox"
                checked={useStationHandoff}
                onChange={(e) => setUseStationHandoff(e.target.checked)}
              />
              Requiere transferencia entre estaciones
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

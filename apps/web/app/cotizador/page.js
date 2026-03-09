"use client";

import { useMemo, useState } from "react";

const zoneFactor = {
  urbana: 1,
  metropolitana: 1.18,
  intermunicipal: 1.35,
};

const serviceFactor = {
  express: 1.3,
  programado: 1,
  recurrente: 0.9,
};

export default function CotizadorPage() {
  const [distanceKm, setDistanceKm] = useState(8);
  const [stops, setStops] = useState(1);
  const [zoneType, setZoneType] = useState("urbana");
  const [serviceType, setServiceType] = useState("programado");

  const estimate = useMemo(() => {
    const base = 49;
    const perKm = 7.5;
    const stopExtra = Math.max(0, stops - 1) * 14;
    const distanceCost = distanceKm * perKm;
    const subtotal = (base + distanceCost + stopExtra) * zoneFactor[zoneType] * serviceFactor[serviceType];
    const total = Math.round(subtotal);
    const etaMin = Math.max(25, Math.round(distanceKm * 5 + stops * 8));
    return { total, etaMin };
  }, [distanceKm, stops, zoneType, serviceType]);

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
        </nav>
      </header>

      <span className="badge">Cotizador Express</span>
      <h1>Estima tu envio en segundos para Tabasco y Campeche.</h1>
      <p className="hero-note">Este cotizador es referencial y ayuda a comparar escenarios por distancia, tipo de zona y nivel de urgencia.</p>

      <section className="panel contact-grid">
        <article className="card">
          <h2>Parametros del servicio</h2>
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
              Numero de paradas
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
              </select>
            </label>
            <label>
              Tipo de servicio
              <select value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
                <option value="programado">Programado</option>
                <option value="express">Express</option>
                <option value="recurrente">Recurrente</option>
              </select>
            </label>
          </form>
        </article>

        <article className="card">
          <h2>Resultado estimado</h2>
          <p className="kpi">Total aproximado: <strong>${estimate.total} MXN</strong></p>
          <p className="kpi">Tiempo estimado: <strong>{estimate.etaMin} min</strong></p>
          <p className="field-hint">El precio final puede variar por horario, saturacion operativa, dimensiones del paquete y politicas vigentes.</p>
          <div className="inline-actions">
            <a className="btn btn-primary" href="/contacto">Solicitar propuesta formal</a>
            <a className="btn" href="/niveles-servicio">Ver niveles de servicio</a>
          </div>
        </article>
      </section>
    </main>
  );
}

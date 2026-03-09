"use client";

import { useMemo, useState } from "react";

const statusByPrefix = {
  REC: "Recibida en estacion",
  RUT: "En ruta de entrega",
  ENT: "Entregada con evidencia",
  INC: "Incidencia registrada",
};

export default function RastreoGuiaPage() {
  const [guideCode, setGuideCode] = useState("");

  const status = useMemo(() => {
    if (!guideCode) return "Ingresa un folio para consultar estado referencial.";
    const prefix = guideCode.toUpperCase().slice(0, 3);
    return statusByPrefix[prefix] || "Folio valido sin estado referencial. Consulta con soporte para detalle.";
  }, [guideCode]);

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

      <span className="badge">Rastreo de Guia</span>
      <h1>Consulta el estado de tu envio con tu folio.</h1>
      <p className="hero-note">Herramienta referencial para consulta rapida. Para trazabilidad completa usa el Portal Cliente o soporte Mande24.</p>

      <section className="panel contact-grid">
        <article className="card">
          <h2>Buscar folio</h2>
          <label>
            Folio de guia
            <input
              value={guideCode}
              onChange={(e) => setGuideCode(e.target.value)}
              placeholder="Ejemplo: RUT-12034"
            />
          </label>
          <p className="field-hint">Prefijos de ejemplo: REC, RUT, ENT, INC.</p>
        </article>

        <article className="card">
          <h2>Estado</h2>
          <p className="kpi"><strong>{status}</strong></p>
          <div className="inline-actions">
            <a className="btn" href="/contacto">Reportar incidencia</a>
            <a className="btn btn-primary" href="/auth">Ingresar al portal</a>
          </div>
        </article>
      </section>
    </main>
  );
}

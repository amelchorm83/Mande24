async function getApiStatus() {
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${api}/api/v1/health`, { cache: "no-store" });
    if (!res.ok) return "offline";
    const data = await res.json();
    return data.status;
  } catch {
    return "offline";
  }
}

export default async function HomePage() {
  const status = await getApiStatus();

  return (
    <main className="shell public-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" />
          <h2>Mande24 Logistics</h2>
        </div>
        <nav className="nav-pills">
          <a className="nav-link active" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/auth">Portal Auth</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Rider</a>
          <a className="nav-link" href="/station">Portal Estacion</a>
        </nav>
      </header>

      <span className="badge">Inicio</span>
      <h1>La red logistica de Tabasco para empresas que necesitan cumplir a tiempo.</h1>
      <p className="hero-note">Mande24 Logistics integra recoleccion, transporte, entrega y monitoreo digital en una operacion unica para negocios, estaciones y repartidores.</p>

      <section className="panel hero-strip">
        <div>
          <h2>Propuesta de valor</h2>
          <p>Combinamos cobertura local, trazabilidad por guia y control operativo para convertir entregas en una ventaja competitiva.</p>
        </div>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/servicios">Ver Servicios</a>
          <a className="btn" href="/cobertura">Cobertura Tabasco</a>
          <a className="btn" href="/noticias">Noticias</a>
        </div>
      </section>

      <section className="panel">
        <h2>Portales Integrados</h2>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/auth">Portal Auth</a>
          <a className="btn" href="/client">Portal Cliente</a>
          <a className="btn" href="/rider">Portal Rider</a>
          <a className="btn" href="/station">Portal Estacion</a>
        </div>
        <p className="field-hint">Cada portal organiza procesos por etapas para reducir errores, acelerar captura y facilitar la operacion por rol.</p>
      </section>

      <section className="panel">
        <h2>Estado del Sistema</h2>
        <p className="kpi">API: <strong>{status === "ok" ? "Conectada" : "Sin conexion"}</strong></p>
        <small>Endpoint operativo: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</small>
      </section>

      <section className="panel">
        <h2>Capacidades Clave</h2>
        <div className="grid">
          <article className="card">
            <h3>Recoleccion y Guia</h3>
            <p>Generacion de guia con datos completos de origen y destino, direccion validada y asignacion operativa.</p>
          </article>
          <article className="card">
            <h3>Seguimiento en Ruta</h3>
            <p>Monitoreo de etapas por rider con evidencia y firma en entrega para trazabilidad total.</p>
          </article>
          <article className="card">
            <h3>Control de Comisiones</h3>
            <p>Concentrado semanal de comisiones para riders y estaciones con cierre administrativo controlado.</p>
          </article>
          <article className="card">
            <h3>Cobertura Tabasco</h3>
            <p>Segmentacion geografica por municipio, codigo postal y colonia para optimizar asignacion de zonas.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

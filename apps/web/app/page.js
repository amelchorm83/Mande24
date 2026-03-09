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
          <a className="nav-link" href="/client">Cliente</a>
          <a className="nav-link" href="/rider">Rider</a>
          <a className="nav-link" href="/station">Estacion</a>
        </nav>
      </header>

      <span className="badge">Inicio</span>
      <h1>Logistica local pensada para Tabasco: rapida, trazable y transparente.</h1>
      <p className="hero-note">Mande24 Logistics coordina recoleccion, ruta, entrega y seguimiento digital para negocios, estaciones y repartidores en una sola plataforma.</p>

      <section className="panel hero-strip">
        <div>
          <h2>Propuesta de valor</h2>
          <p>Operamos ultima milla con trazabilidad por guia, etapas de entrega y paneles de comision para estaciones y riders.</p>
        </div>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/servicios">Ver Servicios</a>
          <a className="btn" href="/cobertura">Cobertura Tabasco</a>
          <a className="btn" href="/noticias">Noticias</a>
        </div>
      </section>

      <section className="panel">
        <h2>Integracion de Portales</h2>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/auth">Portal Auth</a>
          <a className="btn" href="/client">Portal Cliente</a>
          <a className="btn" href="/rider">Portal Rider</a>
          <a className="btn" href="/station">Portal Estacion</a>
        </div>
        <p className="field-hint">Cada portal secciona sus flujos para evitar pantallas planas y mejorar la operacion por rol.</p>
      </section>

      <section className="panel">
        <h2>Estado del Sistema</h2>
        <p className="kpi">API: <strong>{status === "ok" ? "Conectada" : "Sin conexion"}</strong></p>
        <small>NEXT_PUBLIC_API_URL: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</small>
      </section>

      <section className="panel">
        <h2>Resumen de Operacion</h2>
        <div className="grid">
          <article className="card">
            <h3>Recoleccion y Guia</h3>
            <p>Creacion de guia con cliente origen/destino, direccion completa y asignacion de estacion.</p>
          </article>
          <article className="card">
            <h3>Seguimiento en Ruta</h3>
            <p>Actualizacion de etapas por rider con controles de evidencia y firma al entregar.</p>
          </article>
          <article className="card">
            <h3>Control de Comisiones</h3>
            <p>Monitoreo semanal de comisiones para riders y estaciones con cierre administrativo.</p>
          </article>
          <article className="card">
            <h3>Cobertura Tabasco</h3>
            <p>Definicion de zonas y cobertura geografica por municipio, CP y colonia para automatizacion futura.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

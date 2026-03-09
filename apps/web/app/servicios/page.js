export default function ServiciosPage() {
  return (
    <main className="shell public-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" />
          <h2>Mande24 Logistics</h2>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link active" href="/servicios">Servicios</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/client">Portales</a>
        </nav>
      </header>

      <span className="badge">Servicios</span>
      <h1>Servicios de ultima milla para negocios en crecimiento.</h1>
      <p className="hero-note">Diseño propuesto para una oferta clara por tipo de operacion: urgente, programada y recurrente.</p>

      <section className="panel">
        <div className="grid">
          <article className="card">
            <h3>Entrega Express</h3>
            <p>Recolecta y entrega el mismo dia en rutas urbanas de alta prioridad.</p>
            <small>Ideal para farmacias, refacciones y retail local.</small>
          </article>
          <article className="card">
            <h3>Entrega Programada</h3>
            <p>Ventanas de entrega por hora con control de incidencias y trazabilidad.</p>
            <small>Ideal para e-commerce con promesas de horario.</small>
          </article>
          <article className="card">
            <h3>Ruta Recurrente</h3>
            <p>Rutas fijas para reparto semanal o diario con tablero de rendimiento.</p>
            <small>Ideal para distribuidores y mayoristas.</small>
          </article>
          <article className="card">
            <h3>Evidencia Digital</h3>
            <p>Entrega validada por evidencia y firma para reducir reclamaciones.</p>
            <small>Integra historial por guia para auditoria.</small>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Portales Integrados</h2>
        <div className="inline-actions">
          <a className="btn" href="/auth">Auth</a>
          <a className="btn" href="/client">Cliente</a>
          <a className="btn" href="/rider">Rider</a>
          <a className="btn" href="/station">Estacion</a>
        </div>
      </section>
    </main>
  );
}

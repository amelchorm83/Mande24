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
      <h1>Soluciones de ultima milla para operaciones comerciales exigentes.</h1>
      <p className="hero-note">Diseñamos servicios escalables para entregas urgentes, programadas y recurrentes con control operativo en cada etapa.</p>

      <section className="panel">
        <div className="grid">
          <article className="card">
            <h3>Entrega Express</h3>
            <p>Recoleccion y entrega el mismo dia para pedidos de alta prioridad.</p>
            <small>Ideal para farmacias, refacciones, retail y comercio local.</small>
          </article>
          <article className="card">
            <h3>Entrega Programada</h3>
            <p>Programacion por ventanas horarias con seguimiento de incidencias y confirmacion de entrega.</p>
            <small>Ideal para e-commerce y operaciones con promesa de horario.</small>
          </article>
          <article className="card">
            <h3>Ruta Recurrente</h3>
            <p>Rutas fijas diarias o semanales para volumen constante con control de desempeno.</p>
            <small>Ideal para distribuidores, mayoristas y cadenas comerciales.</small>
          </article>
          <article className="card">
            <h3>Evidencia Digital</h3>
            <p>Entrega validada con evidencia y firma para reducir reclamos y mejorar la confianza del cliente final.</p>
            <small>Incluye historial por guia para auditoria y seguimiento.</small>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Operacion Unificada</h2>
        <p className="hero-note">Nuestros portales conectan autenticacion, captura, reparto y comisiones en un mismo flujo digital.</p>
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

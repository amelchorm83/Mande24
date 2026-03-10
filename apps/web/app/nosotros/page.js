const values = [
  {
    title: "Puntualidad Operativa",
    text: "Planificamos rutas por zonas para cumplir promesas de entrega con tiempos realistas y medibles.",
  },
  {
    title: "Transparencia Total",
    text: "Cada guía y etapa se registra para que cliente, estación y equipo operativo compartan la misma información.",
  },
  {
    title: "Mejora Continua",
    text: "Analizamos indicadores de servicio, incidencias y comisiones para optimizar la operación semana tras semana.",
  },
];

export default function NosotrosPage() {
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
          <a className="nav-link" href="/mandaditos">Mandaditos</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link active" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Nosotros</span>
      <h1>Somos un equipo logístico enfocado en resultados de última milla.</h1>
      <p className="hero-note">Mande24 Logistics nace para conectar negocios de Tabasco con una operación confiable, trazable y escalable.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner nosotros Mande24" />

      <section className="panel">
        <h2>Nuestra Historia</h2>
        <p>
          Integramos tecnología operativa, estandarización de procesos y control en campo para resolver una necesidad clara:
          entregas mejor coordinadas, con evidencia y comunicación oportuna.
        </p>
      </section>

      <section className="panel">
        <h2>Valores de Servicio</h2>
        <div className="grid">
          {values.map((item) => (
            <article className="card" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Equipo y Operación</h2>
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Centro operativo Mande24" />
            <div>
              <h3>Centro Operativo</h3>
              <p className="hero-note">Coordinación de rutas, control de guías y seguimiento de cumplimiento diario.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-rider.svg" alt="Equipo de reparto en ruta" />
            <div>
              <h3>Equipo en Campo</h3>
              <p className="hero-note">Riders conectados a la plataforma para reportar etapas y evidencias en tiempo real.</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}

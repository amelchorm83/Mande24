export const metadata = { title: "Centro de Ayuda" };

const faqs = [
  {
    q: "¿Cómo solicito una recolección?",
    a: "Desde Contacto o con tu ejecutivo comercial indicando origen, destino, horario y tipo de servicio.",
  },
  {
    q: "¿Cómo doy seguimiento a una guía?",
    a: "Con el folio de guía en la página de Rastreo o directamente desde el portal cliente.",
  },
  {
    q: "¿Atienden servicios fuera de ciudad?",
    a: "Sí, con planeación intermunicipal según cobertura activa en Tabasco, Campeche, Chiapas, Yucatán y Quintana Roo.",
  },
  {
    q: "¿Qué pasa si no reciben el paquete?",
    a: "Se registra incidencia y se coordina reintento conforme a política comercial.",
  },
];

export default function CentroAyudaPage() {
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
          <a className="nav-link" href="/industrias">Industrias</a>
          <a className="nav-link active" href="/centro-ayuda">Centro de Ayuda</a>
          <a className="nav-link" href="/rastreo-guia">Rastreo</a>
        </nav>
      </header>

      <span className="badge">Centro de Ayuda</span>
      <h1>Respuestas rápidas para clientes y prospectos de Mande24.</h1>

      <section className="panel">
        <h2>Preguntas frecuentes</h2>
        <div className="grid">
          {faqs.map((item) => (
            <article className="card" key={item.q}>
              <h3>{item.q}</h3>
              <p>{item.a}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>¿No encuentras tu respuesta?</h2>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/contacto">Hablar con soporte comercial</a>
          <a className="btn" href="/rastreo-guia">Rastrear una guía</a>
        </div>
      </section>
    </main>
  );
}

const industryData = [
  {
    title: "Retail y comercio local",
    pain: "Picos de demanda en horarios de salida y entregas fallidas por direccion incompleta.",
    solution: "Rutas por zonas, validacion previa de direccion y seguimiento por etapa para reducir incidencias.",
  },
  {
    title: "Farmacia y salud",
    pain: "Necesidad de respuesta rapida para pedidos sensibles y entregas prioritarias.",
    solution: "Servicio express con prioridad operativa y evidencia digital para trazabilidad.",
  },
  {
    title: "Refacciones y autopartes",
    pain: "Paros de taller por falta de pieza y urgencia de reposicion.",
    solution: "Flujo mixto express + programado para surtido inmediato y reposicion diaria.",
  },
  {
    title: "Despachos y oficinas",
    pain: "Traslado constante de documentos, contratos y paquetes entre sucursales.",
    solution: "Mensajeria corporativa con rutas recurrentes y control por guia.",
  },
];

export default function IndustriasPage() {
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
          <a className="nav-link active" href="/industrias">Industrias</a>
          <a className="nav-link" href="/contacto">Contacto</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Soluciones por Industria</span>
      <h1>Esquemas operativos para sectores con necesidades distintas.</h1>
      <p className="hero-note">Mande24 adapta SLA, frecuencia y cobertura por giro para maximizar cumplimiento en Tabasco y Campeche.</p>

      <section className="panel">
        <h2>Diagnostico rapido por giro</h2>
        <div className="grid">
          {industryData.map((industry) => (
            <article className="card" key={industry.title}>
              <h3>{industry.title}</h3>
              <p><strong>Reto comun:</strong> {industry.pain}</p>
              <p><strong>Respuesta Mande24:</strong> {industry.solution}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Como definimos tu esquema</h2>
        <ol className="flow-list">
          <li>Analisis del volumen diario y ventanas de entrega requeridas.</li>
          <li>Segmentacion por zona, tipo de producto y nivel de urgencia.</li>
          <li>Definicion de SLA y tablero de seguimiento por indicadores clave.</li>
        </ol>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/contacto">Solicitar diagnostico comercial</a>
          <a className="btn" href="/niveles-servicio">Revisar niveles de servicio</a>
        </div>
      </section>
    </main>
  );
}

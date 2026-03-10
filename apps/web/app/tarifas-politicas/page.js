const policies = [
  {
    title: "Tarifa base",
    text: "Incluye recolección, traslado y evidencia digital en cobertura urbana definida.",
  },
  {
    title: "Ajuste por distancia",
    text: "Se calcula por kilómetros estimados y complejidad de ruta intermunicipal.",
  },
  {
    title: "Recargos operativos",
    text: "Pueden aplicar en horarios extendidos, días de alta demanda o servicios críticos.",
  },
  {
    title: "Política de reintento",
    text: "Si no hay receptor disponible, se agenda nuevo intento según condiciones comerciales.",
  },
];

export default function TarifasPoliticasPage() {
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
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link active" href="/tarifas-politicas">Tarifas y Políticas</a>
        </nav>
      </header>

      <span className="badge">Tarifas y Políticas</span>
      <h1>Reglas claras para cotizar y operar con mayor confianza.</h1>
      <p className="hero-note">Aquí encuentras criterios generales para estimación comercial y política de servicio en Tabasco y Campeche.</p>

      <section className="panel">
        <h2>Lineamientos principales</h2>
        <div className="grid">
          {policies.map((item) => (
            <article className="card" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Notas comerciales</h2>
        <ul className="flow-list">
          <li>El cotizador web es referencial y no sustituye una propuesta formal.</li>
          <li>Las condiciones finales se definen por volumen, zonas y nivel de SLA.</li>
          <li>Los tiempos de atención pueden variar por clima y saturación operativa.</li>
        </ul>
      </section>
    </main>
  );
}

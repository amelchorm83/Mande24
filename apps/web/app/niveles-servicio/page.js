const slaLevels = [
  {
    level: "SLA Basico",
    promise: "Entrega dentro de ventana programada",
    target: "85% a 92% cumplimiento",
    useCase: "Operaciones estables con prioridad de costo.",
  },
  {
    level: "SLA Plus",
    promise: "Prioridad en servicios express y trazabilidad reforzada",
    target: "92% a 96% cumplimiento",
    useCase: "Negocios con picos de demanda y compromisos de horario.",
  },
  {
    level: "SLA Critico",
    promise: "Atencion preferente y monitoreo operativo extendido",
    target: "96%+ cumplimiento",
    useCase: "Cuentas estrategicas con impacto alto por retraso.",
  },
];

export default function NivelesServicioPage() {
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
          <a className="nav-link active" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/contacto">Contacto</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Niveles de Servicio</span>
      <h1>Define una promesa operativa realista y medible para tus entregas.</h1>
      <p className="hero-note">Esta pagina te ayuda a conversar de SLA con lenguaje claro para clientes, operaciones y comercial.</p>

      <section className="panel">
        <h2>Comparativo SLA</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nivel</th>
                <th>Promesa</th>
                <th>Objetivo</th>
                <th>Uso recomendado</th>
              </tr>
            </thead>
            <tbody>
              {slaLevels.map((item) => (
                <tr key={item.level}>
                  <td>{item.level}</td>
                  <td>{item.promise}</td>
                  <td>{item.target}</td>
                  <td>{item.useCase}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Buenas practicas para cumplir SLA</h2>
        <ol className="flow-list">
          <li>Definir cobertura exacta por zona y horarios de corte por municipio.</li>
          <li>Establecer rutas contingentes para demanda alta o clima adverso.</li>
          <li>Monitorear causas de incumplimiento y ajustar reglas de asignacion semanalmente.</li>
        </ol>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/contacto">Diseñar SLA con Mande24</a>
          <a className="btn" href="/cotizador">Simular costo operativo</a>
        </div>
      </section>
    </main>
  );
}

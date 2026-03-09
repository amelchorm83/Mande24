const tabascoCoverage = [
  { zone: "Centro", municipalities: "Centro, Nacajuca, Jalpa de Mendez" },
  { zone: "Chontalpa", municipalities: "Comalcalco, Cardenas, Huimanguillo" },
  { zone: "Sierra", municipalities: "Teapa, Tacotalpa, Jalapa" },
  { zone: "Rios", municipalities: "Balancan, Tenosique, Emiliano Zapata" },
];

export default function CoberturaPage() {
  return (
    <main className="shell public-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" />
          <h2>Mande24 Logistics</h2>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link active" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/client">Portales</a>
        </nav>
      </header>

      <span className="badge">Cobertura</span>
      <h1>Cobertura activa: solo Tabasco.</h1>
      <p className="hero-note">Propuesta de diseño con enfoque geográfico: cobertura por zonas operativas y expansión planificada.</p>

      <section className="panel">
        <h2>Zonas de Cobertura en Tabasco</h2>
        <div className="grid">
          {tabascoCoverage.map((item) => (
            <article className="card" key={item.zone}>
              <h3>{item.zone}</h3>
              <p>{item.municipalities}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Modelo de expansion</h2>
        <ol className="flow-list">
          <li>Consolidar cobertura por colonia y codigo postal dentro de Tabasco.</li>
          <li>Extender a municipios colindantes con demanda recurrente.</li>
          <li>Integrar reglas automáticas de asignacion por zonas geo en el ERP.</li>
        </ol>
      </section>
    </main>
  );
}

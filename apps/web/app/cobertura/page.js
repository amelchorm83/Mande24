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
      <h1>Cobertura activa en Tabasco con enfoque operativo por zonas.</h1>
      <p className="hero-note">Nuestra operacion actual esta concentrada en Tabasco para asegurar tiempos confiables, control de ruta y calidad de servicio.</p>

      <section className="panel">
        <h2>Zonas Operativas</h2>
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
        <h2>Plan de Expansion</h2>
        <ol className="flow-list">
          <li>Consolidar cobertura por colonia y codigo postal en los municipios activos de Tabasco.</li>
          <li>Escalar a corredores regionales colindantes con demanda sostenida.</li>
          <li>Automatizar asignacion por zonas geograficas dentro del ERP para mejorar tiempos de respuesta.</li>
        </ol>
      </section>
    </main>
  );
}

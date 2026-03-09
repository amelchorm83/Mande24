const coverageByState = [
  {
    state: "Tabasco",
    zones: [
      { zone: "Centro", municipalities: "Centro, Nacajuca, Jalpa de Mendez" },
      { zone: "Chontalpa", municipalities: "Comalcalco, Cardenas, Huimanguillo" },
      { zone: "Sierra", municipalities: "Teapa, Tacotalpa, Jalapa" },
      { zone: "Rios", municipalities: "Balancan, Tenosique, Emiliano Zapata" },
    ],
  },
  {
    state: "Campeche",
    zones: [
      { zone: "Campeche Capital", municipalities: "Campeche, Lerma" },
      { zone: "Carmen", municipalities: "Ciudad del Carmen, Sabancuy" },
      { zone: "Norte", municipalities: "Calkini, Hecelchakan, Tenabo" },
      { zone: "Oriente", municipalities: "Champoton, Escarcega" },
    ],
  },
];

export default function CoberturaPage() {
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
          <a className="nav-link active" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/auth">Portal Auth</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Rider</a>
          <a className="nav-link" href="/station">Portal Estacion</a>
        </nav>
      </header>

      <span className="badge">Cobertura</span>
      <h1>Cobertura activa en Tabasco y Campeche con enfoque operativo por zonas.</h1>
      <p className="hero-note">La cobertura se gestiona por zonas, municipios y capacidad operativa para mantener tiempos confiables y mejor experiencia para cliente final.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner de cobertura Mande24" />

      <section className="panel">
        <h2>Mapa de Cobertura</h2>
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-map.svg" alt="Mapa de cobertura de Tabasco" />
            <div>
              <h3>Operacion Regional</h3>
              <p className="hero-note">Cobertura definida por municipio, codigo postal y colonia para una asignacion mas precisa.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-station.svg" alt="Estacion operativa para zonas" />
            <div>
              <h3>Despacho por Zonas</h3>
              <p className="hero-note">Las estaciones operan bajo reglas geograficas para optimizar cada ruta de entrega.</p>
            </div>
          </article>
        </div>
      </section>

      {coverageByState.map((stateItem) => (
        <section className="panel" key={stateItem.state}>
          <h2>Zonas Operativas: {stateItem.state}</h2>
          <div className="grid">
            {stateItem.zones.map((item) => (
              <article className="card" key={`${stateItem.state}-${item.zone}`}>
                <h3>{item.zone}</h3>
                <p>{item.municipalities}</p>
              </article>
            ))}
          </div>
        </section>
      ))}

      <section className="panel">
        <h2>Promesa de Servicio por Zona</h2>
        <div className="grid">
          <article className="card">
            <h3>Express urbano</h3>
            <p>Atencion prioritaria en zonas urbanas con asignacion rapida de rider.</p>
          </article>
          <article className="card">
            <h3>Programado intermunicipal</h3>
            <p>Ventanas horarias para entregas entre municipios de Tabasco y Campeche.</p>
          </article>
          <article className="card">
            <h3>Rutas recurrentes</h3>
            <p>Planeacion semanal para empresas con volumen estable y entregas frecuentes.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Plan de Expansion</h2>
        <ol className="flow-list">
          <li>Consolidar cobertura por colonia y codigo postal en municipios activos de Tabasco y Campeche.</li>
          <li>Escalar a corredores regionales colindantes con demanda sostenida en sureste.</li>
          <li>Automatizar asignacion por zonas geograficas dentro del ERP para mejorar tiempos de respuesta.</li>
        </ol>
      </section>
    </main>
  );
}

const posts = [
  {
    title: "Mande24 integra SEPOMEX para direccionamiento de alta precision",
    date: "08 Mar 2026",
    excerpt: "La captura de direccion opera con cascada Estado -> Municipio -> CP -> Colonia para disminuir incidencias y devoluciones.",
  },
  {
    title: "Portales rediseñados por etapas operativas",
    date: "08 Mar 2026",
    excerpt: "Cliente, Rider y Estacion evolucionan de vista plana a navegacion por secciones para acelerar procesos clave.",
  },
  {
    title: "Nueva capa de cobertura geografica para automatizacion de zonas",
    date: "08 Mar 2026",
    excerpt: "Las zonas ahora se definen por estado, municipio, codigo postal y colonia para una asignacion mas precisa.",
  },
];

export default function NoticiasPage() {
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
          <a className="nav-link active" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/auth">Portal Auth</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Rider</a>
          <a className="nav-link" href="/station">Portal Estacion</a>
        </nav>
      </header>

      <span className="badge">Noticias</span>
      <h1>Actualizaciones de producto, operacion y cobertura.</h1>
      <p className="hero-note">Publicamos avances clave para clientes, aliados y equipos operativos con enfoque en resultados medibles.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner de noticias Mande24" />

      <section className="panel">
        <div className="grid">
          {posts.map((post) => (
            <article className="card" key={post.title}>
              <small>{post.date}</small>
              <h3>{post.title}</h3>
              <p>{post.excerpt}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Galeria de Avances</h2>
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Actualizacion en centro operativo" />
            <div>
              <h3>Operacion de Hub</h3>
              <p className="hero-note">Nuevas practicas de control para mejorar salida de guias y trazabilidad.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-map.svg" alt="Expansion de cobertura en Tabasco" />
            <div>
              <h3>Expansion Geografica</h3>
              <p className="hero-note">Planeacion por zonas para crecimiento ordenado y respuesta mas rapida.</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}

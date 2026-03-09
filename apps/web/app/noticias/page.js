const posts = [
  {
    title: "Mande24 activa catalogo SEPOMEX para direccionamiento preciso",
    date: "08 Mar 2026",
    excerpt: "Ahora la captura de direccion usa cascada Estado -> Municipio -> CP -> Colonia para reducir errores de entrega.",
  },
  {
    title: "Rediseño de portales por secciones",
    date: "08 Mar 2026",
    excerpt: "Cliente, Rider y Estacion evolucionan de vista plana a navegacion por secciones operativas.",
  },
  {
    title: "Nueva capa de cobertura geográfica en zonas",
    date: "08 Mar 2026",
    excerpt: "Las zonas ahora pueden mapearse por estado, municipio, codigo postal y colonia para automatizaciones futuras.",
  },
];

export default function NoticiasPage() {
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
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link active" href="/noticias">Noticias</a>
          <a className="nav-link" href="/client">Portales</a>
        </nav>
      </header>

      <span className="badge">Noticias</span>
      <h1>Actualizaciones operativas y tecnológicas.</h1>
      <p className="hero-note">Contenido propuesto para comunicar avances de producto, despliegues y cobertura en tiempo real.</p>

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
    </main>
  );
}

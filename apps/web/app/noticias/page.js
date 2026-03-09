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
      <h1>Actualizaciones de producto, operacion y cobertura.</h1>
      <p className="hero-note">Publicamos avances clave para clientes, aliados y equipos operativos con enfoque en resultados medibles.</p>

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

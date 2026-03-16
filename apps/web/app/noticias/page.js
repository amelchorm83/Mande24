export const metadata = { title: "Noticias" };

const posts = [
  {
    title: "Lanzamos Mandaditos 24 para pendientes urgentes en zonas urbanas",
    date: "09 Mar 2026",
    excerpt: "El nuevo servicio atiende compras rápidas, entrega de documentos y artículos olvidados con seguimiento por etapa.",
  },
  {
    title: "Mande24 integra SEPOMEX para direccionamiento de alta precisión",
    date: "08 Mar 2026",
    excerpt: "La captura de dirección opera con cascada Estado -> Municipio -> CP -> Colonia para disminuir incidencias y devoluciones.",
  },
  {
    title: "Portales rediseñados por etapas operativas",
    date: "08 Mar 2026",
    excerpt: "Cliente, Rider y Estación evolucionan de vista plana a navegación por secciones para acelerar procesos clave.",
  },
  {
    title: "Nueva capa de cobertura geográfica para automatización de zonas",
    date: "08 Mar 2026",
    excerpt: "Las zonas ahora se definen por estado, municipio, código postal y colonia para una asignación más precisa.",
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
          <a className="nav-link" href="/mandaditos">Mandaditos</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link active" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/auth">Portal Acceso</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Repartidor</a>
          <a className="nav-link" href="/station">Portal Estación</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Noticias</span>
      <h1>Actualizaciones de producto, operación y cobertura.</h1>
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
        <h2>Galería de Avances</h2>
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-mandaditos.svg" alt="Lanzamiento del servicio de mandaditos" />
            <div>
              <h3>Mandaditos 24 en Operación</h3>
              <p className="hero-note">Cobertura de compras, documentos y urgencias con respuesta rápida y monitoreo digital.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Actualización en centro operativo" />
            <div>
              <h3>Operación de Hub</h3>
              <p className="hero-note">Nuevas prácticas de control para mejorar salida de guías y trazabilidad.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-map.svg" alt="Expansión de cobertura en Tabasco" />
            <div>
              <h3>Expansión Geográfica</h3>
              <p className="hero-note">Planeación por zonas para crecimiento ordenado y respuesta más rápida.</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}

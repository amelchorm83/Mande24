export default function ContactoPage() {
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
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link active" href="/contacto">Contacto</a>
        </nav>
      </header>

      <span className="badge">Contacto</span>
      <h1>Hablemos de tu operacion de entregas.</h1>
      <p className="hero-note">Comparte tus necesidades y te proponemos una solucion de ultima milla para tu negocio en Tabasco.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner contacto Mande24" />

      <section className="panel contact-grid">
        <article className="card">
          <h2>Formulario de Contacto</h2>
          <form className="form-grid">
            <label>
              Nombre completo
              <input placeholder="Tu nombre" />
            </label>
            <label>
              Empresa
              <input placeholder="Nombre de tu empresa" />
            </label>
            <label>
              Correo
              <input type="email" placeholder="correo@empresa.com" />
            </label>
            <label>
              Telefono
              <input placeholder="993 000 0000" />
            </label>
            <label>
              Tipo de servicio
              <select defaultValue="express">
                <option value="express">Entrega Express</option>
                <option value="programada">Entrega Programada</option>
                <option value="recurrente">Ruta Recurrente</option>
              </select>
            </label>
            <label>
              Mensaje
              <textarea rows={5} placeholder="Describe tu operacion y volumen estimado" />
            </label>
            <button className="btn btn-primary" type="submit">Enviar solicitud</button>
          </form>
        </article>

        <article className="card">
          <h2>Canales Directos</h2>
          <p className="hero-note">Tambien puedes contactarnos por WhatsApp para una atencion mas rapida.</p>
          <div className="inline-actions">
            <a className="btn whatsapp-btn" href="https://wa.me/529930000000" target="_blank" rel="noreferrer">WhatsApp Comercial</a>
            <a className="btn" href="mailto:comercial@mande24.com">comercial@mande24.com</a>
          </div>
          <h3>Horario de Atencion</h3>
          <ul className="flow-list">
            <li>Lunes a viernes: 08:00 - 19:00</li>
            <li>Sabado: 09:00 - 14:00</li>
            <li>Domingo: guardias operativas segun contrato</li>
          </ul>
          <img className="hero-banner" src="/brand/photo-station.svg" alt="Equipo de atencion comercial" />
        </article>
      </section>
    </main>
  );
}

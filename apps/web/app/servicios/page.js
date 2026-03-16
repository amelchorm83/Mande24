export const metadata = { title: "Servicios" };

export default function ServiciosPage() {
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
          <a className="nav-link active" href="/servicios">Servicios</a>
          <a className="nav-link" href="/mandaditos">Mandaditos</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
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

      <span className="badge">Servicios</span>
      <h1>Mensajería, paquetería y mandaditos para resolver entregas urgentes todos los días.</h1>
      <p className="hero-note">Diseñamos servicios escalables para empresas y personas que necesitan rapidez, comunicación clara y evidencia de entrega en Tabasco, Campeche, Chiapas, Yucatán y Quintana Roo.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner de servicios Mande24" />

      <section className="panel" id="mandaditos">
        <span className="badge">Mandaditos 24</span>
        <h2>Servicio estrella para pendientes urgentes</h2>
        <div className="contact-grid">
          <div>
            <p className="hero-note">Resolvemos compras rápidas, entrega de documentos, olvidos de llaves, cargadores, medicinas y artículos prioritarios con asignación inmediata.</p>
            <ul className="flow-list">
              <li>Solicitud por contacto directo con datos de origen y destino.</li>
              <li>Asignación del rider disponible más cercano.</li>
              <li>Seguimiento por etapa y confirmación de entrega.</li>
            </ul>
            <div className="inline-actions">
              <a className="btn btn-primary" href="/contacto">Pedir Mandadito</a>
              <a className="btn" href="/cobertura">Ver Cobertura</a>
            </div>
          </div>
          <div className="media-card">
            <img src="/brand/photo-mandaditos.svg" alt="Mandaditos para compras y documentos" />
            <div>
              <h3>Compras y Envío Exprés</h3>
              <p className="hero-note">Ideal para imprevistos de oficina, hogar y negocio que no pueden esperar.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="grid">
          <article className="card">
            <h3>Entrega Express</h3>
            <p>Recolección y entrega el mismo día para pedidos de alta prioridad.</p>
            <small>Ideal para farmacias, refacciones, retail y comercio local.</small>
          </article>
          <article className="card">
            <h3>Mandaditos Urbanos</h3>
            <p>Atención de pendientes puntuales en minutos para personas y negocios con necesidad inmediata.</p>
            <small>Ideal para documentos, compras urgentes y artículos olvidados.</small>
          </article>
          <article className="card">
            <h3>Entrega Programada</h3>
            <p>Programación por ventanas horarias con seguimiento de incidencias y confirmación de entrega.</p>
            <small>Ideal para e-commerce y operaciones con promesa de horario.</small>
          </article>
          <article className="card">
            <h3>Ruta Recurrente</h3>
            <p>Rutas fijas diarias o semanales para volumen constante con control de desempeño.</p>
            <small>Ideal para distribuidores, mayoristas y cadenas comerciales.</small>
          </article>
          <article className="card">
            <h3>Evidencia Digital</h3>
            <p>Entrega validada con evidencia y firma para reducir reclamos y mejorar la confianza del cliente final.</p>
            <small>Incluye historial por guía para auditoría y seguimiento.</small>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Planes para clientes y potenciales clientes</h2>
        <div className="grid">
          <article className="card">
            <h3>Plan Inicial</h3>
            <p>Para negocios que están comenzando su operación de entregas.</p>
            <small>Incluye exprés urbano y reportes básicos por semana.</small>
          </article>
          <article className="card">
            <h3>Plan Crecimiento</h3>
            <p>Para empresas con aumento de volumen y entregas diarias.</p>
            <small>Incluye programadas, recurrentes y prioridad por zona.</small>
          </article>
          <article className="card">
            <h3>Plan Enterprise</h3>
            <p>Para operaciones con múltiples rutas, sucursales y control avanzado.</p>
            <small>Incluye tablero operativo, SLA y seguimiento dedicado.</small>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Qué incluye cada servicio</h2>
        <ol className="flow-list">
          <li>Captura de solicitud con datos de origen, destino y prioridad.</li>
          <li>Asignación operativa según zona de cobertura y disponibilidad.</li>
          <li>Seguimiento por etapas con confirmación de entrega.</li>
          <li>Evidencia digital para control y reducción de reclamos.</li>
        </ol>
      </section>

      <section className="panel">
        <h2>Operación Unificada</h2>
        <p className="hero-note">Nuestros portales conectan autenticación, captura, reparto y comisiones en un mismo flujo digital.</p>
        <div className="inline-actions">
          <a className="btn" href="/auth">Portal Acceso</a>
          <a className="btn" href="/client">Portal Cliente</a>
          <a className="btn" href="/rider">Portal Repartidor</a>
          <a className="btn" href="/station">Portal Estación</a>
        </div>
      </section>

      <section className="panel">
        <h2>FAQ Comercial</h2>
        <div className="grid">
          <article className="card">
            <h3>¿Atienden solo empresas?</h3>
            <p>No. Atendemos empresas, comercios y también solicitudes puntuales de clientes individuales.</p>
          </article>
          <article className="card">
            <h3>¿Pueden operar en dos estados?</h3>
            <p>Sí. Actualmente operamos con cobertura en Tabasco, Campeche, Chiapas, Yucatán y Quintana Roo según zona y disponibilidad.</p>
          </article>
          <article className="card">
            <h3>¿Cómo solicito una propuesta?</h3>
            <p>Desde contacto o WhatsApp comercial. Nuestro equipo arma una propuesta según volumen y tipo de entrega.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Casos Operativos</h2>
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-mandaditos-app.svg" alt="Caso operativo de mandaditos con seguimiento digital" />
            <div>
              <h3>Mandaditos con Trazabilidad</h3>
              <p className="hero-note">Desde la solicitud hasta la entrega final con evidencia y confirmación en tiempo real.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-rider.svg" alt="Servicio express en ruta" />
            <div>
              <h3>Express Urbano</h3>
              <p className="hero-note">Atención de pedidos críticos con seguimiento por etapa y evidencia de entrega.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Operación de hub logístico" />
            <div>
              <h3>Consolidación de Pedidos</h3>
              <p className="hero-note">Control centralizado de salidas para mejorar tiempos de respuesta y productividad.</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}

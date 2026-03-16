async function getApiStatus() {
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${api}/api/v1/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(2000),
    });
    if (!res.ok) return "offline";
    const data = await res.json();
    return data.status;
  } catch {
    return "offline";
  }
}

export default async function HomePage() {
  const status = await getApiStatus();

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
          <a className="nav-link active" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
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

      <span className="badge">Inicio</span>
      <h1>La red logística del sureste para empresas y familias que necesitan resolver entregas al instante.</h1>
      <p className="hero-note">Mande24 Logistics integra mensajería, paquetería y mandaditos con monitoreo digital para una operación rápida, confiable y cercana en Tabasco, Campeche, Chiapas, Yucatán y Quintana Roo.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner operativo Mande24 Logistics" />

      <section className="panel hero-strip">
        <div>
          <h2>Propuesta de valor</h2>
          <p>Combinamos cobertura local, trazabilidad por guía y mandaditos exprés para convertir entregas urgentes en una ventaja competitiva.</p>
        </div>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/servicios">Ver Servicios</a>
          <a className="btn" href="/servicios#mandaditos">Mandaditos 24</a>
          <a className="btn" href="/cobertura">Cobertura Sureste (5 estados)</a>
          <a className="btn" href="/noticias">Noticias</a>
          <a className="btn" href="/contacto">Solicitar cotización</a>
        </div>
      </section>

      <section className="panel">
        <h2>Soluciones por tipo de cliente</h2>
        <div className="grid">
          <article className="card">
            <h3>Negocios con entregas diarias</h3>
            <p>Centraliza tus pedidos en una sola operación con guías, evidencia y reportes de cumplimiento por semana.</p>
            <small>Ideal para retail, farmacias, refaccionarias y distribuidores.</small>
          </article>
          <article className="card">
            <h3>Empresas con picos de demanda</h3>
            <p>Escala en temporadas altas sin perder control de tiempos, prioridades y trazabilidad en ruta.</p>
            <small>Ideal para campañas comerciales y temporadas de alta venta.</small>
          </article>
          <article className="card">
            <h3>Personas y familias</h3>
            <p>Resuelve pendientes urgentes con mandaditos confiables y confirmación digital de entrega.</p>
            <small>Ideal para documentos, compras de último minuto y artículos olvidados.</small>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Cómo funciona en 4 pasos</h2>
        <ol className="flow-list">
          <li>Solicitas servicio por portal o formulario con datos de origen y destino.</li>
          <li>Asignamos rider y ruta según zona de cobertura y prioridad operativa.</li>
          <li>Monitoreas etapas de entrega con evidencia y actualización en tiempo real.</li>
          <li>Recibes confirmación final y, si aplica, documentación para facturación.</li>
        </ol>
      </section>

      <section className="panel">
        <h2>Indicadores que mejoran tu operación</h2>
        <div className="grid">
          <article className="card">
            <h3>Cumplimiento por franja</h3>
            <p>Visualiza entregas a tiempo por ventana horaria para tomar decisiones de capacidad diaria.</p>
          </article>
          <article className="card">
            <h3>Tiempo promedio por zona</h3>
            <p>Identifica colonias o municipios con mayor duracion para ajustar promesa y rutas.</p>
          </article>
          <article className="card">
            <h3>Tasa de reintentos</h3>
            <p>Mide incidencias de direccion o ausencia del receptor para reducir costos operativos.</p>
          </article>
          <article className="card">
            <h3>Productividad por rider</h3>
            <p>Compara servicios completados por turno con evidencia digital para gestion objetiva.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Modelos de servicio por necesidad</h2>
        <div className="grid">
          <article className="card">
            <h3>Última milla para e-commerce</h3>
            <p>Despacho diario con horarios comprometidos, evidencia y atención de incidencias.</p>
          </article>
          <article className="card">
            <h3>Mensajería corporativa</h3>
            <p>Rutas internas para contratos, documentos legales y entregas entre sucursales.</p>
          </article>
          <article className="card">
            <h3>Farmacia y salud</h3>
            <p>Servicios prioritarios para medicamentos y productos sensibles con seguimiento puntual.</p>
          </article>
          <article className="card">
            <h3>Refacciones y retail</h3>
            <p>Operación mixta exprés y programada para piezas urgentes y reposición en tienda.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Mandaditos 24: Servicio Destacado</h2>
        <div className="contact-grid">
          <div>
            <p className="hero-note">Atendemos compras de último minuto, envío de documentos, olvidos en casa u oficina y entregas urgentes en zonas urbanas del sureste.</p>
            <div className="inline-actions">
              <a className="btn btn-primary" href="/contacto">Solicitar Mandadito</a>
              <a className="btn" href="/servicios#mandaditos">Ver Cobertura y Tiempos</a>
            </div>
          </div>
          <div className="media-card">
            <img src="/brand/photo-mandaditos.svg" alt="Servicio de mandaditos de Mande24" />
            <div>
              <h3>Respuesta Rápida</h3>
              <p className="hero-note">Asignación de rider y seguimiento claro desde la solicitud hasta la entrega final.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Portales Integrados</h2>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/auth">Portal Acceso</a>
          <a className="btn" href="/client">Portal Cliente</a>
          <a className="btn" href="/rider">Portal Repartidor</a>
          <a className="btn" href="/station">Portal Estación</a>
        </div>
        <p className="field-hint">Cada portal organiza procesos por etapas para reducir errores, acelerar captura y facilitar la operación por rol.</p>
      </section>

      <section className="panel">
        <h2>Estado del Sistema</h2>
        <p className="kpi">API: <strong>{status === "ok" ? "Conectada" : "Sin conexión"}</strong></p>
        <small>Endpoint operativo: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</small>
      </section>

      <section className="panel">
        <h2>Capacidades Clave</h2>
        <div className="grid">
          <article className="card">
            <h3>Recolección y Guía</h3>
            <p>Generación de guía con datos completos de origen y destino, dirección validada y asignación operativa.</p>
          </article>
          <article className="card">
            <h3>Seguimiento en Ruta</h3>
            <p>Monitoreo de etapas por rider con evidencia y firma en entrega para trazabilidad total.</p>
          </article>
          <article className="card">
            <h3>Control de Comisiones</h3>
            <p>Concentrado semanal de comisiones para riders y estaciones con cierre administrativo controlado.</p>
          </article>
          <article className="card">
            <h3>Cobertura Sureste: 5 estados</h3>
            <p>Segmentación geográfica por municipio, código postal y colonia para optimizar asignación de zonas en toda la región.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Nuevas páginas con funcionalidad e información</h2>
        <p className="hero-note">Explora herramientas nuevas para cotizar, definir niveles de servicio, identificar tu esquema por industria y consultar ayuda operativa.</p>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/cotizador">Cotizador Express</a>
          <a className="btn" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="btn" href="/industrias">Soluciones por Industria</a>
          <a className="btn" href="/casos-exito">Casos de Éxito</a>
          <a className="btn" href="/tarifas-politicas">Tarifas y Políticas</a>
          <a className="btn" href="/centro-ayuda">Centro de Ayuda</a>
          <a className="btn" href="/rastreo-guia">Rastreo de Guía</a>
        </div>
      </section>

      <section className="panel">
        <h2>Preguntas frecuentes</h2>
        <div className="grid">
          <article className="card">
            <h3>¿Cuánto tardan en asignar un servicio?</h3>
            <p>La asignación depende de zona y demanda, pero en servicios exprés suele hacerse en minutos.</p>
          </article>
          <article className="card">
            <h3>¿Puedo programar rutas semanales?</h3>
            <p>Sí. Diseñamos rutas recurrentes para operaciones con volumen estable por día o por semana.</p>
          </article>
          <article className="card">
            <h3>¿Atienden empresas y clientes individuales?</h3>
            <p>Sí. Tenemos esquemas para negocio y también para solicitudes puntuales de clientes finales.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Operación en Imágenes</h2>
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Centro logístico de Mande24" />
            <div>
              <h3>Centro Operativo</h3>
              <p className="hero-note">Coordinación de guías, control de salida y trazabilidad de cada entrega.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-rider.svg" alt="Rider en ruta de entrega" />
            <div>
              <h3>Rider en Ruta</h3>
              <p className="hero-note">Actualización de etapas en tiempo real para mejorar la comunicación con el cliente.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-station.svg" alt="Estación con indicadores de comisión" />
            <div>
              <h3>Estación y Comisiones</h3>
              <p className="hero-note">Monitoreo semanal con indicadores claros para decisiones operativas rápidas.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-mandaditos-app.svg" alt="Flujo digital del servicio de mandaditos" />
            <div>
              <h3>Mandaditos en Minutos</h3>
              <p className="hero-note">Flujo ágil para resolver pendientes urgentes con evidencia y confirmación digital.</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}

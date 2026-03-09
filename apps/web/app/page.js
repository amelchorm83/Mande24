async function getApiStatus() {
  const api = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${api}/api/v1/health`, { cache: "no-store" });
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
          <a className="nav-link" href="/auth">Portal Auth</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Rider</a>
          <a className="nav-link" href="/station">Portal Estacion</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Inicio</span>
      <h1>La red logistica de Tabasco y Campeche para empresas y familias que necesitan resolver entregas al instante.</h1>
      <p className="hero-note">Mande24 Logistics integra mensajeria, paqueteria y mandaditos con monitoreo digital para una operacion rapida, confiable y cercana en Tabasco y Campeche.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner operativo Mande24 Logistics" />

      <section className="panel hero-strip">
        <div>
          <h2>Propuesta de valor</h2>
          <p>Combinamos cobertura local, trazabilidad por guia y mandaditos express para convertir entregas urgentes en una ventaja competitiva.</p>
        </div>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/servicios">Ver Servicios</a>
          <a className="btn" href="/servicios#mandaditos">Mandaditos 24</a>
          <a className="btn" href="/cobertura">Cobertura Tabasco y Campeche</a>
          <a className="btn" href="/noticias">Noticias</a>
          <a className="btn" href="/contacto">Solicitar cotizacion</a>
        </div>
      </section>

      <section className="panel">
        <h2>Soluciones por tipo de cliente</h2>
        <div className="grid">
          <article className="card">
            <h3>Negocios con entregas diarias</h3>
            <p>Centraliza tus pedidos en una sola operacion con guias, evidencia y reportes de cumplimiento por semana.</p>
            <small>Ideal para retail, farmacias, refaccionarias y distribuidores.</small>
          </article>
          <article className="card">
            <h3>Empresas con picos de demanda</h3>
            <p>Escala en temporadas altas sin perder control de tiempos, prioridades y trazabilidad en ruta.</p>
            <small>Ideal para campañas comerciales y temporadas de alta venta.</small>
          </article>
          <article className="card">
            <h3>Personas y familias</h3>
            <p>Resuelve pendientes urgentes con mandaditos confiables y confirmacion digital de entrega.</p>
            <small>Ideal para documentos, compras de ultimo minuto y articulos olvidados.</small>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Como funciona en 4 pasos</h2>
        <ol className="flow-list">
          <li>Solicitas servicio por portal o formulario con datos de origen y destino.</li>
          <li>Asignamos rider y ruta segun zona de cobertura y prioridad operativa.</li>
          <li>Monitoreas etapas de entrega con evidencia y actualizacion en tiempo real.</li>
          <li>Recibes confirmacion final y, si aplica, documentacion para facturacion.</li>
        </ol>
      </section>

      <section className="panel">
        <h2>Indicadores que mejoran tu operacion</h2>
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
            <h3>Ultima milla para e-commerce</h3>
            <p>Despacho diario con horarios comprometidos, evidencia y atencion de incidencias.</p>
          </article>
          <article className="card">
            <h3>Mensajeria corporativa</h3>
            <p>Rutas internas para contratos, documentos legales y entregas entre sucursales.</p>
          </article>
          <article className="card">
            <h3>Farmacia y salud</h3>
            <p>Servicios prioritarios para medicamentos y productos sensibles con seguimiento puntual.</p>
          </article>
          <article className="card">
            <h3>Refacciones y retail</h3>
            <p>Operacion mixta express y programada para piezas urgentes y reposicion en tienda.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Mandaditos 24: Servicio Destacado</h2>
        <div className="contact-grid">
          <div>
            <p className="hero-note">Atendemos compras de ultimo minuto, envio de documentos, olvidos en casa u oficina y entregas urgentes en zonas urbanas de Tabasco.</p>
            <div className="inline-actions">
              <a className="btn btn-primary" href="/contacto">Solicitar Mandadito</a>
              <a className="btn" href="/servicios#mandaditos">Ver Cobertura y Tiempos</a>
            </div>
          </div>
          <div className="media-card">
            <img src="/brand/photo-mandaditos.svg" alt="Servicio de mandaditos de Mande24" />
            <div>
              <h3>Respuesta Rapida</h3>
              <p className="hero-note">Asignacion de rider y seguimiento claro desde la solicitud hasta la entrega final.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Portales Integrados</h2>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/auth">Portal Auth</a>
          <a className="btn" href="/client">Portal Cliente</a>
          <a className="btn" href="/rider">Portal Rider</a>
          <a className="btn" href="/station">Portal Estacion</a>
        </div>
        <p className="field-hint">Cada portal organiza procesos por etapas para reducir errores, acelerar captura y facilitar la operacion por rol.</p>
      </section>

      <section className="panel">
        <h2>Estado del Sistema</h2>
        <p className="kpi">API: <strong>{status === "ok" ? "Conectada" : "Sin conexion"}</strong></p>
        <small>Endpoint operativo: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</small>
      </section>

      <section className="panel">
        <h2>Capacidades Clave</h2>
        <div className="grid">
          <article className="card">
            <h3>Recoleccion y Guia</h3>
            <p>Generacion de guia con datos completos de origen y destino, direccion validada y asignacion operativa.</p>
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
            <h3>Cobertura Tabasco y Campeche</h3>
            <p>Segmentacion geografica por municipio, codigo postal y colonia para optimizar asignacion de zonas en ambos estados.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Nuevas paginas con funcionalidad e informacion</h2>
        <p className="hero-note">Explora herramientas nuevas para cotizar, definir niveles de servicio, identificar tu esquema por industria y consultar ayuda operativa.</p>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/cotizador">Cotizador Express</a>
          <a className="btn" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="btn" href="/industrias">Soluciones por Industria</a>
          <a className="btn" href="/casos-exito">Casos de Exito</a>
          <a className="btn" href="/tarifas-politicas">Tarifas y Politicas</a>
          <a className="btn" href="/centro-ayuda">Centro de Ayuda</a>
          <a className="btn" href="/rastreo-guia">Rastreo de Guia</a>
        </div>
      </section>

      <section className="panel">
        <h2>Preguntas frecuentes</h2>
        <div className="grid">
          <article className="card">
            <h3>Cuanto tardan en asignar un servicio?</h3>
            <p>La asignacion depende de zona y demanda, pero en servicios express suele hacerse en minutos.</p>
          </article>
          <article className="card">
            <h3>Puedo programar rutas semanales?</h3>
            <p>Si. Diseñamos rutas recurrentes para operaciones con volumen estable por dia o por semana.</p>
          </article>
          <article className="card">
            <h3>Atienden empresas y clientes individuales?</h3>
            <p>Si. Tenemos esquemas para negocio y tambien para solicitudes puntuales de clientes finales.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <h2>Operacion en Imagenes</h2>
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Centro logistico de Mande24" />
            <div>
              <h3>Centro Operativo</h3>
              <p className="hero-note">Coordinacion de guias, control de salida y trazabilidad de cada entrega.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-rider.svg" alt="Rider en ruta de entrega" />
            <div>
              <h3>Rider en Ruta</h3>
              <p className="hero-note">Actualizacion de etapas en tiempo real para mejorar la comunicacion con el cliente.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-station.svg" alt="Estacion con indicadores de comision" />
            <div>
              <h3>Estacion y Comisiones</h3>
              <p className="hero-note">Monitoreo semanal con indicadores claros para decisiones operativas rapidas.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-mandaditos-app.svg" alt="Flujo digital del servicio de mandaditos" />
            <div>
              <h3>Mandaditos en Minutos</h3>
              <p className="hero-note">Flujo agil para resolver pendientes urgentes con evidencia y confirmacion digital.</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}

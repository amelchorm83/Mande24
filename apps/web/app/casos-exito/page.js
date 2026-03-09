const cases = [
  {
    name: "Cadena de farmacias regional",
    challenge: "Pedidos urgentes al cierre de turno con alto riesgo de atraso.",
    approach: "Modelo mixto express + programado con prioridad por zona urbana.",
    result: "Reduccion estimada de 28% en entregas fuera de tiempo en 8 semanas.",
  },
  {
    name: "Refaccionaria con entrega a talleres",
    challenge: "Paros por falta de piezas criticas en horarios pico.",
    approach: "Rutas recurrentes por corredor y soporte express para urgencias.",
    result: "Mejora estimada de 22% en tiempos de reposicion.",
  },
  {
    name: "Comercio local con e-commerce",
    challenge: "Variacion diaria de volumen y baja trazabilidad de incidencias.",
    approach: "Tablero de seguimiento por guia y gestion de reintentos.",
    result: "Aumento estimado de 19% en cumplimiento semanal.",
  },
];

export default function CasosExitoPage() {
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
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a>
          <a className="nav-link active" href="/casos-exito">Casos de Exito</a>
        </nav>
      </header>

      <span className="badge">Casos de Exito</span>
      <h1>Resultados operativos que muestran el impacto de una ultima milla bien ejecutada.</h1>
      <p className="hero-note">Estos casos son referenciales y sirven para visualizar mejoras medibles en cumplimiento, tiempos y control de incidencias.</p>

      <section className="panel">
        <h2>Historias de operacion</h2>
        <div className="grid">
          {cases.map((item) => (
            <article className="card" key={item.name}>
              <h3>{item.name}</h3>
              <p><strong>Reto:</strong> {item.challenge}</p>
              <p><strong>Estrategia:</strong> {item.approach}</p>
              <p><strong>Resultado:</strong> {item.result}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Que medimos para mejorar</h2>
        <ol className="flow-list">
          <li>Cumplimiento por franja horaria y por municipio.</li>
          <li>Tiempo promedio por ruta y causa principal de retraso.</li>
          <li>Tasa de reintentos y entregas exitosas al primer intento.</li>
        </ol>
      </section>
    </main>
  );
}

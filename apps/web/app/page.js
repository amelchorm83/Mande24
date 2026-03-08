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
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" />
          <h2>Mande24 Independent</h2>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/auth">Auth</a>
          <a className="nav-link" href="/client">Cliente</a>
          <a className="nav-link" href="/rider">Rider</a>
          <a className="nav-link" href="/station">Estacion</a>
        </nav>
      </header>

      <span className="badge">Panel Principal</span>
      <h1>Plataforma Independiente Mande24</h1>
      <p className="hero-note">Interfaz de operacion para autenticar usuarios, crear guias, actualizar entregas y cerrar comisiones semanales.</p>

      <section className="panel">
        <h2>Entrar a Portales</h2>
        <div className="inline-actions">
          <a className="btn btn-primary" href="/auth">1) Auth</a>
          <a className="btn" href="/client">2) Cliente</a>
          <a className="btn" href="/rider">3) Rider</a>
          <a className="btn" href="/station">4) Estacion</a>
        </div>
        <ol className="flow-list">
          <li>Inicia en Auth para guardar token.</li>
          <li>Crea una guia en Cliente y copia el Delivery ID.</li>
          <li>Actualiza etapas en Rider hasta delivered.</li>
          <li>Consulta y cierra semana en Estacion.</li>
        </ol>
      </section>

      <section className="panel">
        <h2>Estado del sistema</h2>
        <p className="kpi">API: <strong>{status === "ok" ? "Conectada" : "Sin conexion"}</strong></p>
        <small>NEXT_PUBLIC_API_URL: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}</small>
      </section>

      <section className="panel">
        <h2>Que puedes operar aqui</h2>
        <div className="grid">
          <article className="card">
            <h3>Cliente</h3>
            <p>Alta de guia con precio automatico segun servicio y estacion.</p>
          </article>
          <article className="card">
            <h3>Rider</h3>
            <p>Control de etapa de entrega con regla de evidencia y firma.</p>
          </article>
          <article className="card">
            <h3>Estacion</h3>
            <p>Vista semanal de comisiones y cierre administrativo.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AuthPage() {
  const [section, setSection] = useState("acceso");
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("admin.ops@mande24.local");
  const [fullName, setFullName] = useState("Admin Ops");
  const [password, setPassword] = useState("Secret123");
  const [role, setRole] = useState("admin");
  const [token, setToken] = useState("");
  const [msg, setMsg] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setMsg("Procesando...");

    try {
      if (mode === "register") {
        const registerRes = await fetch(`${API_BASE}/api/v1/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, full_name: fullName, password, role }),
        });
        if (!registerRes.ok && registerRes.status !== 409) {
          const err = await registerRes.text();
          setMsg(`Registro fallido: ${err}`);
          return;
        }
      }

      const loginRes = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!loginRes.ok) {
        const err = await loginRes.text();
        setMsg(`Login fallido: ${err}`);
        return;
      }

      const data = await loginRes.json();
      setToken(data.access_token);
      localStorage.setItem("m24_token", data.access_token);
      localStorage.setItem("m24_role", role);
      localStorage.setItem("m24_email", email);
      setMsg("Autenticado. Token guardado en navegador.");
    } catch (error) {
      setMsg(`Error: ${error.message}`);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <img className="brand-logo" src="/brand/icon.svg" alt="Icono Mande24" />
          <div className="brand-copy">
            <h2>ERPMande24</h2>
            <p className="brand-slogan">Acceso central para operación y control.</p>
          </div>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link active" href="/auth">Portal Auth</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Rider</a>
          <a className="nav-link" href="/station">Portal Estación</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Portal Auth</span>
      <h1>Acceso Seguro y Gestión de Token</h1>
      <p className="hero-note">Inicia sesión o registra usuarios operativos. El token se almacena en el navegador para habilitar los demás portales automáticamente.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner portal auth" />

      <section className="panel">
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-station.svg" alt="Panel de control y accesos" />
            <div>
              <h3>Control de Accesos</h3>
              <p className="hero-note">Centraliza la autenticación para mantener continuidad en todos los portales operativos.</p>
            </div>
          </article>
        </div>
      </section>

      <nav className="section-nav">
        <button className={section === "acceso" ? "section-link active" : "section-link"} onClick={() => setSection("acceso")}>Acceso</button>
        <button className={section === "flujo" ? "section-link active" : "section-link"} onClick={() => setSection("flujo")}>Flujo Operativo</button>
      </nav>

      {section === "acceso" && <section className="panel">
        <div className="inline-actions">
          <button className={mode === "login" ? "btn btn-primary" : "btn"} onClick={() => setMode("login")}>Login</button>
          <button className={mode === "register" ? "btn btn-primary" : "btn"} onClick={() => setMode("register")}>Register + Login</button>
        </div>
        <p className="field-hint">Roles habilitados: `admin`, `station`, `rider`, `client`.</p>

        <form className="form-grid" onSubmit={onSubmit}>
          <label>
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>

          {mode === "register" && (
            <label>
              Nombre completo
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </label>
          )}

          <label>
            Password
            <input value={password} type="password" onChange={(e) => setPassword(e.target.value)} required />
          </label>

          {mode === "register" && (
            <label>
              Rol
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="admin">Administrador</option>
                <option value="station">Estación</option>
                <option value="rider">Repartidor</option>
                <option value="client">Cliente</option>
              </select>
            </label>
          )}

          <button className="btn btn-primary" type="submit">{mode === "login" ? "Entrar" : "Crear y Entrar"}</button>
        </form>

        <p className={`status-line ${msg.includes("fallido") || msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
        {token && <textarea className="mono-box" value={token} readOnly rows={6} />}
      </section>}

      {section === "flujo" && <section className="panel">
        <h2>Flujo recomendado</h2>
        <ol className="flow-list">
          <li>Autentica con usuario `admin` para configurar catálogos y parámetros iniciales.</li>
          <li>Continúa en `Cliente` para registrar perfiles y crear guías.</li>
          <li>Da seguimiento en `Rider` para actualizar etapas de entrega.</li>
        </ol>
      </section>}
    </main>
  );
}

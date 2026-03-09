"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ContactoPage() {
  const [fullName, setFullName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [serviceInterest, setServiceInterest] = useState("express");
  const [message, setMessage] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [isSending, setIsSending] = useState(false);

  async function onSubmit(ev) {
    ev.preventDefault();
    setIsSending(true);
    setStatusMsg("Enviando solicitud...");

    try {
      const res = await fetch(`${API_BASE}/api/v1/public/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          company,
          email,
          phone,
          service_interest: serviceInterest,
          message,
        }),
      });
      const data = await res.json();

      if (!res.ok) {
        setStatusMsg(`No se pudo enviar: ${JSON.stringify(data)}`);
        return;
      }

      setStatusMsg(data.message || "Solicitud enviada correctamente.");
      setFullName("");
      setCompany("");
      setEmail("");
      setPhone("");
      setServiceInterest("express");
      setMessage("");
    } catch (error) {
      setStatusMsg(`Error de red: ${error.message}`);
    } finally {
      setIsSending(false);
    }
  }

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
          <form className="form-grid" onSubmit={onSubmit}>
            <label>
              Nombre completo
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Tu nombre" required />
            </label>
            <label>
              Empresa
              <input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Nombre de tu empresa" />
            </label>
            <label>
              Correo
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="correo@empresa.com" required />
            </label>
            <label>
              Telefono
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="993 000 0000" />
            </label>
            <label>
              Tipo de servicio
              <select value={serviceInterest} onChange={(e) => setServiceInterest(e.target.value)}>
                <option value="express">Entrega Express</option>
                <option value="programada">Entrega Programada</option>
                <option value="recurrente">Ruta Recurrente</option>
              </select>
            </label>
            <label>
              Mensaje
              <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={5} placeholder="Describe tu operacion y volumen estimado" required minLength={10} />
            </label>
            <button className="btn btn-primary" type="submit" disabled={isSending}>{isSending ? "Enviando..." : "Enviar solicitud"}</button>
          </form>
          <p className={`status-line ${statusMsg.includes("No se pudo") || statusMsg.includes("Error") ? "warn" : "ok"}`}>{statusMsg}</p>
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

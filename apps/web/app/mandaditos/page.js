"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MandaditosPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [pickupAddress, setPickupAddress] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [itemType, setItemType] = useState("documentos");
  const [urgency, setUrgency] = useState("hoy");
  const [notes, setNotes] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [isSending, setIsSending] = useState(false);

  async function onSubmit(ev) {
    ev.preventDefault();
    setIsSending(true);
    setStatusMsg("Enviando solicitud de mandadito...");

    const detailMessage = [
      `Servicio: Mandaditos 24`,
      `Tipo: ${itemType}`,
      `Urgencia: ${urgency}`,
      `Origen: ${pickupAddress}`,
      `Destino: ${deliveryAddress}`,
      notes ? `Notas: ${notes}` : "",
    ]
      .filter(Boolean)
      .join(" | ");

    try {
      const res = await fetch(`${API_BASE}/api/v1/public/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          company: "Solicitud Web Mandaditos",
          email,
          phone,
          service_interest: "mandaditos",
          message: detailMessage,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setStatusMsg(`No se pudo enviar: ${JSON.stringify(data)}`);
        return;
      }

      setStatusMsg(data.message || "Mandadito solicitado correctamente. Te contactamos en breve.");
      setFullName("");
      setEmail("");
      setPhone("");
      setPickupAddress("");
      setDeliveryAddress("");
      setItemType("documentos");
      setUrgency("hoy");
      setNotes("");
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
          <a className="nav-link active" href="/mandaditos">Mandaditos</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/contacto">Contacto</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Mandaditos 24</span>
      <h1>Resuelve pendientes urgentes en minutos.</h1>
      <p className="hero-note">Compras rapidas, documentos, articulos olvidados y envios puntuales con seguimiento claro de principio a fin.</p>
      <img className="hero-banner" src="/brand/photo-mandaditos.svg" alt="Servicio de mandaditos Mande24" />

      <section className="panel contact-grid">
        <article className="card">
          <h2>Solicita tu Mandadito</h2>
          <form className="form-grid" onSubmit={onSubmit}>
            <label>
              Nombre completo
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Tu nombre" required />
            </label>
            <label>
              Correo
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="correo@dominio.com" required />
            </label>
            <label>
              Telefono
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="993 000 0000" required />
            </label>
            <label>
              Direccion de origen
              <input value={pickupAddress} onChange={(e) => setPickupAddress(e.target.value)} placeholder="Donde recogemos" required />
            </label>
            <label>
              Direccion de destino
              <input value={deliveryAddress} onChange={(e) => setDeliveryAddress(e.target.value)} placeholder="Donde entregamos" required />
            </label>
            <label>
              Tipo de mandadito
              <select value={itemType} onChange={(e) => setItemType(e.target.value)}>
                <option value="documentos">Documentos</option>
                <option value="compras">Compras rapidas</option>
                <option value="medicinas">Medicinas</option>
                <option value="articulo_olvidado">Articulo olvidado</option>
              </select>
            </label>
            <label>
              Urgencia
              <select value={urgency} onChange={(e) => setUrgency(e.target.value)}>
                <option value="hoy">Hoy</option>
                <option value="en_2_horas">En las proximas 2 horas</option>
                <option value="programado">Programado</option>
              </select>
            </label>
            <label>
              Notas adicionales
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} placeholder="Referencia, instrucciones o detalles de entrega" />
            </label>
            <button className="btn btn-primary" type="submit" disabled={isSending}>{isSending ? "Enviando..." : "Solicitar Mandadito"}</button>
          </form>
          <p className={`status-line ${statusMsg.includes("No se pudo") || statusMsg.includes("Error") ? "warn" : "ok"}`}>{statusMsg}</p>
        </article>

        <article className="card">
          <h2>Que puedes resolver</h2>
          <ul className="flow-list">
            <li>Envio de documentos urgentes entre oficinas.</li>
            <li>Compra y entrega de articulos de ultimo minuto.</li>
            <li>Recuperacion de objetos olvidados en casa o negocio.</li>
            <li>Entregas puntuales con evidencia digital.</li>
          </ul>
          <div className="inline-actions">
            <a className="btn" href="/servicios">Ver todos los servicios</a>
            <a className="btn" href="/cobertura">Consultar cobertura</a>
          </div>
          <img className="hero-banner" src="/brand/photo-mandaditos-app.svg" alt="Seguimiento digital de mandaditos" />
        </article>
      </section>
    </main>
  );
}

"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RiderPortalPage() {
  const [token, setToken] = useState("");
  const [deliveryId, setDeliveryId] = useState("");
  const [stage, setStage] = useState("in_transit");
  const [hasEvidence, setHasEvidence] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem("m24_token") || "");
  }, []);

  async function updateStage(e) {
    e.preventDefault();
    if (!deliveryId) {
      setMsg("Ingresa delivery_id");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/guides/deliveries/${deliveryId}/stage`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ stage, has_evidence: hasEvidence, has_signature: hasSignature }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error: ${JSON.stringify(data)}`);
        return;
      }
      setMsg(`Entrega actualizada: ${data.stage}`);
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

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
          <a className="nav-link active" href="/rider">Rider</a>
          <a className="nav-link" href="/station">Estacion</a>
        </nav>
      </header>

      <span className="badge">Portal Rider</span>
      <h1>Seguimiento de Entrega</h1>
      <p className="hero-note">Pega el <code>delivery_id</code> generado en Cliente y avanza la entrega por etapas. Para <code>delivered</code> debes marcar evidencia y firma.</p>

      <section className="panel">
        <h2>Actualizar etapa</h2>
        <form className="form-grid" onSubmit={updateStage}>
          <label>
            Token Bearer
            <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
          </label>
          <label>
            Delivery ID
            <input value={deliveryId} onChange={(e) => setDeliveryId(e.target.value)} required />
          </label>
          <label>
            Nueva etapa
            <select value={stage} onChange={(e) => setStage(e.target.value)}>
              <option value="assigned">assigned</option>
              <option value="picked_up">picked_up</option>
              <option value="in_transit">in_transit</option>
              <option value="at_station">at_station</option>
              <option value="out_for_delivery">out_for_delivery</option>
              <option value="delivered">delivered</option>
              <option value="failed">failed</option>
            </select>
          </label>
          <label className="check-row">
            <input type="checkbox" checked={hasEvidence} onChange={(e) => setHasEvidence(e.target.checked)} />
            Evidencia
          </label>
          <label className="check-row">
            <input type="checkbox" checked={hasSignature} onChange={(e) => setHasSignature(e.target.checked)} />
            Firma
          </label>
          <button className="btn btn-primary" type="submit">Actualizar etapa</button>
        </form>
        <p className={`status-line ${msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
      </section>

      <section className="panel">
        <h2>Guia rapida de etapas</h2>
        <ol className="flow-list">
          <li><code>assigned</code> -&gt; pedido asignado.</li>
          <li><code>picked_up</code> y <code>in_transit</code> -&gt; en movimiento.</li>
          <li><code>delivered</code> -&gt; marcar <code>Evidencia</code> y <code>Firma</code> para validar cierre.</li>
        </ol>
      </section>
    </main>
  );
}

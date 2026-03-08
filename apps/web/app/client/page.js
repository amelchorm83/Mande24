"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ClientPortalPage() {
  const [token, setToken] = useState("");
  const [services, setServices] = useState([]);
  const [stations, setStations] = useState([]);
  const [customerName, setCustomerName] = useState("Cliente Portal");
  const [destinationName, setDestinationName] = useState("Destino Portal");
  const [serviceId, setServiceId] = useState("");
  const [stationId, setStationId] = useState("");
  const [guideResult, setGuideResult] = useState(null);
  const [deliveryId, setDeliveryId] = useState("");
  const [msg, setMsg] = useState("");

  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, "Content-Type": "application/json" }),
    [token]
  );

  useEffect(() => {
    const saved = localStorage.getItem("m24_token") || "";
    setToken(saved);
  }, []);

  async function loadCatalogs() {
    if (!token) {
      setMsg("Necesitas token. Ve primero a /auth.");
      return;
    }
    try {
      const [svcRes, stRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/catalogs/services`, { headers }),
        fetch(`${API_BASE}/api/v1/catalogs/stations`, { headers }),
      ]);
      if (!svcRes.ok || !stRes.ok) {
        setMsg("No se pudieron cargar catalogos. Revisa tu token/rol.");
        return;
      }
      const svcData = await svcRes.json();
      const stData = await stRes.json();
      setServices(svcData);
      setStations(stData);
      if (svcData.length && !serviceId) setServiceId(svcData[0].id);
      if (stData.length && !stationId) setStationId(stData[0].id);
      setMsg("Catalogos cargados.");
    } catch (error) {
      setMsg(`Error catalogos: ${error.message}`);
    }
  }

  async function createGuide(e) {
    e.preventDefault();
    if (!serviceId || !stationId) {
      setMsg("Selecciona servicio y estacion.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/guides`, {
        method: "POST",
        headers,
        body: JSON.stringify({ customer_name: customerName, destination_name: destinationName, service_id: serviceId, station_id: stationId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error creando guia: ${JSON.stringify(data)}`);
        return;
      }

      const deliveriesRes = await fetch(`${API_BASE}/api/v1/guides/${data.guide_code}/deliveries`, { headers });
      if (deliveriesRes.ok) {
        const deliveries = await deliveriesRes.json();
        if (deliveries.length) {
          setDeliveryId(deliveries[0].delivery_id);
        }
      }

      setGuideResult(data);
      setMsg("Guia creada correctamente.");
    } catch (error) {
      setMsg(`Error creando guia: ${error.message}`);
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
          <a className="nav-link active" href="/client">Cliente</a>
          <a className="nav-link" href="/rider">Rider</a>
          <a className="nav-link" href="/station">Estacion</a>
        </nav>
      </header>

      <span className="badge">Portal Cliente</span>
      <h1>Crear Guia Operativa</h1>
      <p className="hero-note">Este portal crea una guia y te devuelve el `delivery_id` necesario para que el rider continue el flujo.</p>

      <section className="panel">
        <h2>Paso 1: Token y catalogos</h2>
        <label>
          Token Bearer
          <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
        </label>
        <p className="field-hint">Si no tienes token, ve a `Auth` y entra con tu usuario.</p>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={() => localStorage.setItem("m24_token", token)}>Guardar token</button>
          <button className="btn btn-primary" onClick={loadCatalogs}>Cargar catalogos</button>
        </div>
      </section>

      <section className="panel">
        <h2>Paso 2: Crear guia</h2>
        <form className="form-grid" onSubmit={createGuide}>
          <label>
            Nombre cliente
            <input value={customerName} onChange={(e) => setCustomerName(e.target.value)} required />
          </label>
          <label>
            Nombre destino
            <input value={destinationName} onChange={(e) => setDestinationName(e.target.value)} required />
          </label>
          <label>
            Servicio
            <select value={serviceId} onChange={(e) => setServiceId(e.target.value)}>
              <option value="">Selecciona</option>
              {services.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
          </label>
          <label>
            Estacion
            <select value={stationId} onChange={(e) => setStationId(e.target.value)}>
              <option value="">Selecciona</option>
              {stations.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
          </label>
          <button className="btn btn-primary" type="submit">Crear guia</button>
        </form>

        {guideResult && (
          <div className="result-box">
            <p><strong>Guia:</strong> {guideResult.guide_code}</p>
            <p><strong>Venta:</strong> {guideResult.sale_amount} {guideResult.currency}</p>
            {deliveryId && <p><strong>Delivery ID:</strong> {deliveryId}</p>}
            {deliveryId && <p className="field-hint">Siguiente paso: abre `Rider` y pega este Delivery ID para cambiar etapas.</p>}
          </div>
        )}
        <p className={`status-line ${msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
      </section>
    </main>
  );
}

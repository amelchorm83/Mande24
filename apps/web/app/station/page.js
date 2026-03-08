"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StationPortalPage() {
  const [token, setToken] = useState("");
  const [riderRows, setRiderRows] = useState([]);
  const [stationRows, setStationRows] = useState([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem("m24_token") || "");
  }, []);

  async function fetchCommissions() {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [ridersRes, stationsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/commissions/riders/weekly`, { headers }),
        fetch(`${API_BASE}/api/v1/commissions/stations/weekly`, { headers }),
      ]);
      if (!ridersRes.ok || !stationsRes.ok) {
        setMsg("No se pudieron obtener comisiones. Revisa rol/token.");
        return;
      }
      const riders = await ridersRes.json();
      const stations = await stationsRes.json();
      setRiderRows(riders.rows || []);
      setStationRows(stations.rows || []);
      setMsg("Comisiones cargadas.");
    } catch (error) {
      setMsg(`Error: ${error.message}`);
    }
  }

  async function closeWeek() {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [ridersClose, stationsClose] = await Promise.all([
        fetch(`${API_BASE}/api/v1/commissions/riders/weekly/close`, { method: "POST", headers }),
        fetch(`${API_BASE}/api/v1/commissions/stations/weekly/close`, { method: "POST", headers }),
      ]);
      if (!ridersClose.ok || !stationsClose.ok) {
        setMsg("No se pudo cerrar semana. Revisa rol admin/token.");
        return;
      }
      setMsg("Semana cerrada y snapshots guardados.");
      await fetchCommissions();
    } catch (error) {
      setMsg(`Error cierre: ${error.message}`);
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
          <a className="nav-link" href="/rider">Rider</a>
          <a className="nav-link active" href="/station">Estacion</a>
        </nav>
      </header>

      <span className="badge">Portal Estacion</span>
      <h1>Comisiones Semanales</h1>
      <p className="hero-note">Consulta resultados en vivo de riders y estaciones. Solo rol admin puede ejecutar cierre semanal.</p>

      <section className="panel">
        <h2>Acciones</h2>
        <label>
          Token Bearer
          <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
        </label>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={fetchCommissions}>Cargar comisiones</button>
          <button className="btn btn-primary" onClick={closeWeek}>Cerrar semana</button>
        </div>
        <p className={`status-line ${msg.includes("No se pudo") || msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
        <div className="inline-actions">
          <span className="kpi">Riders: <strong>{riderRows.length}</strong></span>
          <span className="kpi">Estaciones: <strong>{stationRows.length}</strong></span>
        </div>
      </section>

      <section className="panel">
        <h2>Rider Weekly</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Rider ID</th><th>Entregas</th><th>Total</th></tr>
            </thead>
            <tbody>
              {riderRows.map((row) => (
                <tr key={row.rider_id}><td>{row.rider_id}</td><td>{row.delivery_count}</td><td>{row.total_amount}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Station Weekly</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Station ID</th><th>Guias</th><th>Venta</th><th>Total</th></tr>
            </thead>
            <tbody>
              {stationRows.map((row) => (
                <tr key={row.station_id}><td>{row.station_id}</td><td>{row.sold_guide_count}</td><td>{row.sold_guide_amount}</td><td>{row.total_amount}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

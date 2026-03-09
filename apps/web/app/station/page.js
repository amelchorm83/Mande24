"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StationPortalPage() {
  const [section, setSection] = useState("clientes");
  const [token, setToken] = useState("");
  const [riderRows, setRiderRows] = useState([]);
  const [stationRows, setStationRows] = useState([]);
  const [states, setStates] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);
  const [postalCodes, setPostalCodes] = useState([]);
  const [colonies, setColonies] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [newClientName, setNewClientName] = useState("");
  const [newClientKind, setNewClientKind] = useState("destination");
  const [stateCode, setStateCode] = useState("");
  const [municipalityCode, setMunicipalityCode] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [colonyId, setColonyId] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [wantsInvoice, setWantsInvoice] = useState(false);
  const [createPortalAccess, setCreatePortalAccess] = useState(true);
  const [portalEmail, setPortalEmail] = useState("");
  const [portalPassword, setPortalPassword] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem("m24_token") || "");
  }, []);

  useEffect(() => {
    if (!token) return;
    loadGeoStates();
    loadProfiles();
  }, [token]);

  useEffect(() => {
    if (!token || !stateCode) return;
    loadMunicipalities(stateCode);
  }, [token, stateCode]);

  useEffect(() => {
    if (!token || !municipalityCode) return;
    loadPostalCodes(municipalityCode);
  }, [token, municipalityCode]);

  useEffect(() => {
    if (!token || !stateCode || !municipalityCode || !postalCode) return;
    loadColonies(stateCode, municipalityCode, postalCode);
  }, [token, stateCode, municipalityCode, postalCode]);

  async function loadGeoStates() {
    const headers = { Authorization: `Bearer ${token}` };
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/states`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    setStates(rows);
    if (!stateCode && rows.length) setStateCode(rows[0].code);
  }

  async function loadMunicipalities(code) {
    const headers = { Authorization: `Bearer ${token}` };
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/municipalities?state_code=${encodeURIComponent(code)}`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    setMunicipalities(rows);
    setMunicipalityCode(rows.length ? rows[0].code : "");
    setPostalCodes([]);
    setPostalCode("");
    setColonies([]);
    setColonyId("");
  }

  async function loadPostalCodes(code) {
    const headers = { Authorization: `Bearer ${token}` };
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/postal-codes?municipality_code=${encodeURIComponent(code)}`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    setPostalCodes(rows);
    setPostalCode(rows.length ? rows[0].code : "");
    setColonies([]);
    setColonyId("");
  }

  async function loadColonies(state, municipality, postal) {
    const headers = { Authorization: `Bearer ${token}` };
    const q = new URLSearchParams({
      state_code: state,
      municipality_code: municipality,
      postal_code: postal,
    });
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/colonies?${q.toString()}`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    setColonies(rows);
    setColonyId(rows.length ? rows[0].id : "");
  }

  async function loadProfiles() {
    const headers = { Authorization: `Bearer ${token}` };
    const res = await fetch(`${API_BASE}/api/v1/clients/profiles`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    setProfiles(rows);
  }

  async function createClientProfile(e) {
    e.preventDefault();
    if (!newClientName || !stateCode || !municipalityCode || !postalCode || !colonyId) {
      setMsg("Completa nombre, estado, municipio, CP y colonia para registrar cliente.");
      return;
    }
    const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
    const payload = {
      display_name: newClientName,
      client_kind: newClientKind,
      state_code: stateCode,
      municipality_code: municipalityCode,
      postal_code: postalCode,
      colony_id: colonyId,
      address_line: addressLine,
      wants_invoice: wantsInvoice,
      create_portal_access: createPortalAccess,
      email: createPortalAccess ? portalEmail : null,
      password: createPortalAccess ? portalPassword : null,
    };
    const res = await fetch(`${API_BASE}/api/v1/clients/profiles`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setMsg(`Error alta cliente: ${JSON.stringify(data)}`);
      return;
    }
    setMsg("Cliente registrado desde estacion.");
    setNewClientName("");
    setAddressLine("");
    setColonyId("");
    setPortalEmail("");
    setPortalPassword("");
    await loadProfiles();
  }

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
          <h2>ERPMande24</h2>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/auth">Auth</a>
          <a className="nav-link" href="/client">Cliente</a>
          <a className="nav-link" href="/rider">Rider</a>
          <a className="nav-link active" href="/station">Estacion</a>
        </nav>
      </header>

      <span className="badge">Portal Estacion</span>
      <h1>Control Semanal de Comisiones</h1>
      <p className="hero-note">Consulta resultados de riders y estaciones en tiempo real. El cierre semanal requiere rol `admin`.</p>

      <nav className="section-nav">
        <button className={section === "clientes" ? "section-link active" : "section-link"} onClick={() => setSection("clientes")}>Alta de Clientes</button>
        <button className={section === "comisiones" ? "section-link active" : "section-link"} onClick={() => setSection("comisiones")}>Comisiones</button>
        <button className={section === "resultados" ? "section-link active" : "section-link"} onClick={() => setSection("resultados")}>Resultados</button>
      </nav>

      {section === "clientes" && <section className="panel">
        <h2>Registro de Clientes (Origen/Destino)</h2>
        <form className="form-grid" onSubmit={createClientProfile}>
          <label>
            Nombre cliente
            <input value={newClientName} onChange={(e) => setNewClientName(e.target.value)} required />
          </label>
          <label>
            Tipo cliente
            <select value={newClientKind} onChange={(e) => setNewClientKind(e.target.value)}>
              <option value="origin">Origen</option>
              <option value="destination">Destino</option>
              <option value="both">Ambos</option>
            </select>
          </label>
          <label>
            Estado
            <select value={stateCode} onChange={(e) => setStateCode(e.target.value)}>
              {states.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Municipio
            <select value={municipalityCode} onChange={(e) => setMunicipalityCode(e.target.value)}>
              {municipalities.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Codigo postal
            <select value={postalCode} onChange={(e) => setPostalCode(e.target.value)}>
              {postalCodes.map((item) => <option key={item.code} value={item.code}>{item.code}</option>)}
            </select>
          </label>
          <label>
            Colonia
            <select value={colonyId} onChange={(e) => setColonyId(e.target.value)}>
              <option value="">Selecciona</option>
              {colonies.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Calle y numero
            <input value={addressLine} onChange={(e) => setAddressLine(e.target.value)} />
          </label>
          <label>
            Facturar servicios origen
            <select value={wantsInvoice ? "true" : "false"} onChange={(e) => setWantsInvoice(e.target.value === "true")}>
              <option value="true">Si</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            Crear acceso portal cliente destino
            <select value={createPortalAccess ? "true" : "false"} onChange={(e) => setCreatePortalAccess(e.target.value === "true")}>
              <option value="false">No</option>
              <option value="true">Si</option>
            </select>
          </label>
          {createPortalAccess && (
            <>
              <label>
                Email portal
                <input value={portalEmail} onChange={(e) => setPortalEmail(e.target.value)} required />
              </label>
              <label>
                Password portal
                <input type="password" value={portalPassword} onChange={(e) => setPortalPassword(e.target.value)} required />
              </label>
            </>
          )}
          <button className="btn btn-primary" type="submit">Registrar cliente</button>
        </form>
      </section>}

      {section === "comisiones" && <section className="panel">
        <h2>Acciones de Comision</h2>
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
      </section>}

      {section === "resultados" && <section className="panel">
        <h2>Resumen Semanal Rider</h2>
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
      </section>}

      {section === "resultados" && <section className="panel">
        <h2>Resumen Semanal Estacion</h2>
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
      </section>}

      {section === "resultados" && <section className="panel">
        <h2>Clientes Registrados</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Nombre</th><th>Tipo</th><th>Estado</th><th>Municipio</th><th>CP</th><th>Colonia</th><th>Factura</th></tr>
            </thead>
            <tbody>
              {profiles.map((row) => (
                <tr key={row.id}>
                  <td>{row.display_name}</td><td>{row.client_kind}</td><td>{row.state_code}</td><td>{row.municipality_code}</td><td>{row.postal_code}</td><td>{row.colony_name || "-"}</td><td>{row.wants_invoice ? "Si" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>}
    </main>
  );
}

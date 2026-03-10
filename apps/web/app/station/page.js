"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function StationPortalPage() {
  const [section, setSection] = useState("clientes");
  const [token, setToken] = useState("");
  const [riderRows, setRiderRows] = useState([]);
  const [stationRows, setStationRows] = useState([]);
  const [riderLegRows, setRiderLegRows] = useState([]);
  const [stationLegRows, setStationLegRows] = useState([]);
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
  const [landlinePhone, setLandlinePhone] = useState("");
  const [whatsappPhone, setWhatsappPhone] = useState("");
  const [wantsInvoice, setWantsInvoice] = useState(false);
  const [createPortalAccess, setCreatePortalAccess] = useState(true);
  const [portalEmail, setPortalEmail] = useState("");
  const [portalPassword, setPortalPassword] = useState("");
  const [zones, setZones] = useState([]);
  const [newRiderName, setNewRiderName] = useState("");
  const [newRiderEmail, setNewRiderEmail] = useState("");
  const [newRiderPassword, setNewRiderPassword] = useState("");
  const [newRiderZoneId, setNewRiderZoneId] = useState("");
  const [newRiderVehicle, setNewRiderVehicle] = useState("motorcycle");
  const [newRiderLandline, setNewRiderLandline] = useState("");
  const [newRiderWhatsapp, setNewRiderWhatsapp] = useState("");
  const [newStationName, setNewStationName] = useState("");
  const [newStationZoneId, setNewStationZoneId] = useState("");
  const [newStationLandline, setNewStationLandline] = useState("");
  const [newStationWhatsapp, setNewStationWhatsapp] = useState("");
  const [riderCatalogRows, setRiderCatalogRows] = useState([]);
  const [stationCatalogRows, setStationCatalogRows] = useState([]);
  const [routeGuideCode, setRouteGuideCode] = useState("");
  const [routeLegRows, setRouteLegRows] = useState([]);
  const [routeLegId, setRouteLegId] = useState("");
  const [routeLegRiderId, setRouteLegRiderId] = useState("");
  const [routeLegStatus, setRouteLegStatus] = useState("assigned");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem("m24_token") || "");
  }, []);

  useEffect(() => {
    if (!token) return;
    loadGeoStates();
    loadProfiles();
    loadZones();
    loadCatalogRows();
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
      landline_phone: landlinePhone,
      whatsapp_phone: whatsappPhone,
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
    setMsg("Cliente registrado desde estación.");
    setNewClientName("");
    setAddressLine("");
    setLandlinePhone("");
    setWhatsappPhone("");
    setColonyId("");
    setPortalEmail("");
    setPortalPassword("");
    await loadProfiles();
  }

  async function loadZones() {
    const headers = { Authorization: `Bearer ${token}` };
    const res = await fetch(`${API_BASE}/api/v1/catalogs/zones`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    setZones(rows);
    if (!newRiderZoneId && rows.length) setNewRiderZoneId(rows[0].id);
    if (!newStationZoneId && rows.length) setNewStationZoneId(rows[0].id);
  }

  async function loadCatalogRows() {
    const headers = { Authorization: `Bearer ${token}` };
    const [ridersRes, stationsRes] = await Promise.all([
      fetch(`${API_BASE}/api/v1/catalogs/riders`, { headers }),
      fetch(`${API_BASE}/api/v1/catalogs/stations`, { headers }),
    ]);
    if (ridersRes.ok) setRiderCatalogRows(await ridersRes.json());
    if (stationsRes.ok) setStationCatalogRows(await stationsRes.json());
  }

  async function createRider(e) {
    e.preventDefault();
    if (!newRiderName || !newRiderEmail || !newRiderPassword) {
      setMsg("Completa nombre, email y password del repartidor.");
      return;
    }
    const authHeaders = { "Content-Type": "application/json" };
    const catalogHeaders = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

    const registerRes = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: "POST",
      headers: authHeaders,
      body: JSON.stringify({
        email: newRiderEmail,
        full_name: newRiderName,
        password: newRiderPassword,
        role: "rider",
      }),
    });
    if (!registerRes.ok && registerRes.status !== 409) {
      const err = await registerRes.text();
      setMsg(`Error registro de repartidor: ${err}`);
      return;
    }

    const usersRes = await fetch(`${API_BASE}/ERPMande24/users?q=${encodeURIComponent(newRiderEmail)}`);
    const usersHtml = await usersRes.text();
    const match = usersHtml.match(/\/ERPMande24\/users\/([a-f0-9]{32})/);
    if (!match) {
      setMsg("No se encontro usuario rider recien creado para vincular catalogo.");
      return;
    }

    const riderRes = await fetch(`${API_BASE}/api/v1/catalogs/riders`, {
      method: "POST",
      headers: catalogHeaders,
      body: JSON.stringify({
        user_id: match[1],
        zone_id: newRiderZoneId || null,
        vehicle_type: newRiderVehicle,
        landline_phone: newRiderLandline,
        whatsapp_phone: newRiderWhatsapp,
      }),
    });
    const riderData = await riderRes.json();
    if (!riderRes.ok && !String(JSON.stringify(riderData)).includes("already exists")) {
      setMsg(`Error alta rider catalogo: ${JSON.stringify(riderData)}`);
      return;
    }

    setMsg("Repartidor registrado con telefono fijo y WhatsApp.");
    setNewRiderName("");
    setNewRiderEmail("");
    setNewRiderPassword("");
    setNewRiderLandline("");
    setNewRiderWhatsapp("");
    await loadCatalogRows();
  }

  async function createStation(e) {
    e.preventDefault();
    if (!newStationName || !newStationZoneId) {
      setMsg("Completa nombre y zona de estación.");
      return;
    }
    const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
    const res = await fetch(`${API_BASE}/api/v1/catalogs/stations`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        name: newStationName,
        zone_id: newStationZoneId,
        landline_phone: newStationLandline,
        whatsapp_phone: newStationWhatsapp,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setMsg(`Error alta estación: ${JSON.stringify(data)}`);
      return;
    }
    setMsg("Estación registrada con teléfono fijo y WhatsApp.");
    setNewStationName("");
    setNewStationLandline("");
    setNewStationWhatsapp("");
    await loadCatalogRows();
  }

  async function fetchCommissions() {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [ridersRes, stationsRes, riderLegRes, stationLegRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/commissions/riders/weekly`, { headers }),
        fetch(`${API_BASE}/api/v1/commissions/stations/weekly`, { headers }),
        fetch(`${API_BASE}/api/v1/commissions/riders/weekly/by-leg`, { headers }),
        fetch(`${API_BASE}/api/v1/commissions/stations/weekly/by-leg`, { headers }),
      ]);
      if (!ridersRes.ok || !stationsRes.ok || !riderLegRes.ok || !stationLegRes.ok) {
        setMsg("No se pudieron obtener comisiones. Revisa rol/token.");
        return;
      }
      const riders = await ridersRes.json();
      const stations = await stationsRes.json();
      const ridersByLeg = await riderLegRes.json();
      const stationsByLeg = await stationLegRes.json();
      setRiderRows(riders.rows || []);
      setStationRows(stations.rows || []);
      setRiderLegRows(ridersByLeg.rows || []);
      setStationLegRows(stationsByLeg.rows || []);
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

  async function loadRouteLegs() {
    if (!token || !routeGuideCode) {
      setMsg("Captura token y código de guía para consultar ruta.");
      return;
    }
    try {
      const code = encodeURIComponent(routeGuideCode.trim().toUpperCase());
      const res = await fetch(`${API_BASE}/api/v1/guides/${code}/route-legs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error consultando ruta: ${JSON.stringify(data)}`);
        return;
      }
      setRouteLegRows(data);
      setRouteLegId(data.length ? data[0].id : "");
      setRouteLegRiderId(data.length && data[0].assigned_rider_id ? data[0].assigned_rider_id : "");
      setMsg(`Ruta cargada: ${data.length} tramos.`);
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

  async function updateRouteLeg(e) {
    e.preventDefault();
    if (!token || !routeLegId) {
      setMsg("Selecciona tramo y token valido.");
      return;
    }
    try {
      const payload = {
        status: routeLegStatus,
        rider_id: routeLegRiderId || null,
      };
      const res = await fetch(`${API_BASE}/api/v1/guides/route-legs/${routeLegId}/assign`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error actualizando tramo: ${JSON.stringify(data)}`);
        return;
      }
      setMsg(`Tramo ${data.sequence} actualizado a ${data.status}`);
      await loadRouteLegs();
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

  async function suggestRiderForRouteLeg() {
    if (!token || !routeLegId) {
      setMsg("Selecciona tramo y token valido para sugerir rider.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/guides/route-legs/${routeLegId}/suggest-riders`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error sugiriendo rider: ${JSON.stringify(data)}`);
        return;
      }
      if (!data.length) {
        setMsg("No hay riders activos para sugerir.");
        return;
      }
      setRouteLegRiderId(data[0].rider_id);
      setMsg(`Sugerido rider ${data[0].rider_id} (${data[0].reason}).`);
    } catch (error) {
      setMsg(`Error de red: ${error.message}`);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <img className="brand-logo" src="/brand/icon.svg" alt="Icono Mande24" />
          <div className="brand-copy">
            <h2>Portal Estación</h2>
            <p className="brand-slogan">Control semanal y desempeño operativo.</p>
          </div>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/auth">Portal Acceso</a>
          <a className="nav-link" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Repartidor</a>
          <a className="nav-link active" href="/station">Portal Estación</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Portal Estación</span>
      <h1>Control Semanal de Comisiones</h1>
      <p className="hero-note">Consulta resultados de riders y estaciones en tiempo real. El cierre semanal requiere rol `admin`.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner portal estación" />

      <section className="panel">
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-station.svg" alt="Panel de estación y comisiones" />
            <div>
              <h3>Tablero de Comisiones</h3>
              <p className="hero-note">Visualiza avances semanales y ejecuta cierres administrativos con mayor claridad.</p>
            </div>
          </article>
        </div>
      </section>

      <nav className="section-nav">
        <button className={section === "clientes" ? "section-link active" : "section-link"} onClick={() => setSection("clientes")}>Alta de Clientes</button>
        <button className={section === "riders" ? "section-link active" : "section-link"} onClick={() => setSection("riders")}>Alta de Repartidores</button>
        <button className={section === "estaciones" ? "section-link active" : "section-link"} onClick={() => setSection("estaciones")}>Alta de Estaciones</button>
        <button className={section === "rutas" ? "section-link active" : "section-link"} onClick={() => setSection("rutas")}>Rutas</button>
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
            Código postal
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
            Calle y número
            <input value={addressLine} onChange={(e) => setAddressLine(e.target.value)} />
          </label>
          <label>
            Teléfono fijo
            <input value={landlinePhone} onChange={(e) => setLandlinePhone(e.target.value)} />
          </label>
          <label>
            WhatsApp
            <input value={whatsappPhone} onChange={(e) => setWhatsappPhone(e.target.value)} />
          </label>
          <label>
            Facturar servicios origen
            <select value={wantsInvoice ? "true" : "false"} onChange={(e) => setWantsInvoice(e.target.value === "true")}>
              <option value="true">Sí</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            Crear acceso portal cliente destino
            <select value={createPortalAccess ? "true" : "false"} onChange={(e) => setCreatePortalAccess(e.target.value === "true")}>
              <option value="false">No</option>
              <option value="true">Sí</option>
            </select>
          </label>
          {createPortalAccess && (
            <>
              <label>
                Email portal
                <input value={portalEmail} onChange={(e) => setPortalEmail(e.target.value)} required />
              </label>
              <label>
                Contrasena portal
                <input type="password" value={portalPassword} onChange={(e) => setPortalPassword(e.target.value)} required />
              </label>
            </>
          )}
          <button className="btn btn-primary" type="submit">Registrar cliente</button>
        </form>
      </section>}

      {section === "riders" && <section className="panel">
        <h2>Alta de Repartidores</h2>
        <form className="form-grid" onSubmit={createRider}>
          <label>
            Nombre completo
            <input value={newRiderName} onChange={(e) => setNewRiderName(e.target.value)} required />
          </label>
          <label>
            Email
            <input type="email" value={newRiderEmail} onChange={(e) => setNewRiderEmail(e.target.value)} required />
          </label>
          <label>
            Contrasena
            <input type="password" value={newRiderPassword} onChange={(e) => setNewRiderPassword(e.target.value)} required minLength={8} />
          </label>
          <label>
            Zona
            <select value={newRiderZoneId} onChange={(e) => setNewRiderZoneId(e.target.value)}>
              <option value="">Sin zona</option>
              {zones.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Vehículo
            <input value={newRiderVehicle} onChange={(e) => setNewRiderVehicle(e.target.value)} />
          </label>
          <label>
            Teléfono fijo
            <input value={newRiderLandline} onChange={(e) => setNewRiderLandline(e.target.value)} />
          </label>
          <label>
            WhatsApp
            <input value={newRiderWhatsapp} onChange={(e) => setNewRiderWhatsapp(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit">Registrar repartidor</button>
        </form>
      </section>}

      {section === "estaciones" && <section className="panel">
        <h2>Alta de Estaciones</h2>
        <form className="form-grid" onSubmit={createStation}>
          <label>
            Nombre estación
            <input value={newStationName} onChange={(e) => setNewStationName(e.target.value)} required />
          </label>
          <label>
            Zona
            <select value={newStationZoneId} onChange={(e) => setNewStationZoneId(e.target.value)} required>
              <option value="">Selecciona zona</option>
              {zones.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Teléfono fijo
            <input value={newStationLandline} onChange={(e) => setNewStationLandline(e.target.value)} />
          </label>
          <label>
            WhatsApp
            <input value={newStationWhatsapp} onChange={(e) => setNewStationWhatsapp(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit">Registrar estación</button>
        </form>
      </section>}

      {section === "rutas" && <section className="panel">
        <h2>Asignación Operativa de Rutas</h2>
        <div className="form-grid">
          <label>
            Token de acceso (Bearer)
            <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
          </label>
          <label>
            Código de guía
            <input value={routeGuideCode} onChange={(e) => setRouteGuideCode(e.target.value)} placeholder="M24-20260310-XXXXXX" />
          </label>
        </div>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={loadRouteLegs}>Cargar ruta</button>
          <button className="btn" onClick={suggestRiderForRouteLeg}>Sugerir repartidor por zona</button>
        </div>

        <form className="form-grid" onSubmit={updateRouteLeg}>
          <label>
            Tramo
            <select value={routeLegId} onChange={(e) => setRouteLegId(e.target.value)}>
              <option value="">Selecciona tramo</option>
              {routeLegRows.map((row) => (
                <option key={row.id} value={row.id}>#{row.sequence} {row.leg_type} | {row.status}</option>
              ))}
            </select>
          </label>
          <label>
            Repartidor asignado
            <select value={routeLegRiderId} onChange={(e) => setRouteLegRiderId(e.target.value)}>
              <option value="">Sin asignar</option>
              {riderCatalogRows.filter((row) => row.active).map((row) => (
                <option key={row.id} value={row.id}>{row.id} | user:{row.user_id}</option>
              ))}
            </select>
          </label>
          <label>
            Estado tramo
            <select value={routeLegStatus} onChange={(e) => setRouteLegStatus(e.target.value)}>
              <option value="assigned">Asignado</option>
              <option value="in_progress">En progreso</option>
              <option value="completed">Completado</option>
              <option value="failed">Fallido</option>
              <option value="cancelled">Cancelado</option>
            </select>
          </label>
          <button className="btn btn-primary" type="submit">Actualizar tramo</button>
        </form>

        <div className="table-wrap">
          <table>
            <thead><tr><th>Secuencia</th><th>Tipo</th><th>Estado</th><th>Repartidor</th><th>Est. origen</th><th>Est. destino</th></tr></thead>
            <tbody>
              {routeLegRows.map((row) => (
                <tr key={row.id}><td>{row.sequence}</td><td>{row.leg_type}</td><td>{row.status}</td><td>{row.assigned_rider_id || "-"}</td><td>{row.origin_station_id || "-"}</td><td>{row.destination_station_id || "-"}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className={`status-line ${msg.includes("Error") || msg.includes("No se pudo") ? "warn" : "ok"}`}>{msg}</p>
      </section>}

      {section === "comisiones" && <section className="panel">
        <h2>Acciones de Comisión</h2>
        <label>
          Token de acceso (Bearer)
          <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
        </label>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={fetchCommissions}>Cargar comisiones</button>
          <button className="btn btn-primary" onClick={closeWeek}>Cerrar semana</button>
        </div>
        <p className={`status-line ${msg.includes("No se pudo") || msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
        <div className="inline-actions">
          <span className="kpi">Repartidores: <strong>{riderRows.length}</strong></span>
          <span className="kpi">Estaciones: <strong>{stationRows.length}</strong></span>
          <span className="kpi">Repartidores por tramo: <strong>{riderLegRows.length}</strong></span>
          <span className="kpi">Estaciones por tramo: <strong>{stationLegRows.length}</strong></span>
        </div>
      </section>}

      {section === "resultados" && <section className="panel">
        <h2>Resumen Semanal de Repartidores</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID repartidor</th><th>Entregas</th><th>Total</th></tr>
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
        <h2>Resumen Semanal Estación</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID estacion</th><th>Guias</th><th>Venta</th><th>Total</th></tr>
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
        <h2>Comision de Repartidor por Tipo de Tramo</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID repartidor</th><th>Tipo tramo</th><th>Cantidad</th><th>Total</th></tr>
            </thead>
            <tbody>
              {riderLegRows.map((row, idx) => (
                <tr key={`${row.rider_id}-${row.leg_type}-${idx}`}><td>{row.rider_id}</td><td>{row.leg_type}</td><td>{row.leg_count}</td><td>{row.total_amount}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>}

      {section === "resultados" && <section className="panel">
        <h2>Comision de Estacion por Tipo de Tramo</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID estacion</th><th>Tipo tramo</th><th>Cantidad</th><th>Total</th></tr>
            </thead>
            <tbody>
              {stationLegRows.map((row, idx) => (
                <tr key={`${row.station_id}-${row.leg_type}-${idx}`}><td>{row.station_id}</td><td>{row.leg_type}</td><td>{row.leg_count}</td><td>{row.total_amount}</td></tr>
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
              <tr><th>Nombre</th><th>Tipo</th><th>Estado</th><th>Municipio</th><th>CP</th><th>Colonia</th><th>Telefono fijo</th><th>WhatsApp</th><th>Factura</th></tr>
            </thead>
            <tbody>
              {profiles.map((row) => (
                <tr key={row.id}>
                  <td>{row.display_name}</td><td>{row.client_kind}</td><td>{row.state_code}</td><td>{row.municipality_code}</td><td>{row.postal_code}</td><td>{row.colony_name || "-"}</td><td>{row.landline_phone || "-"}</td><td>{row.whatsapp_phone || "-"}</td><td>{row.wants_invoice ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>}

      {section === "resultados" && <section className="panel">
        <h2>Catálogo de Repartidores</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID</th><th>ID usuario</th><th>Zona</th><th>Telefono fijo</th><th>WhatsApp</th><th>Vehiculo</th><th>Activo</th></tr>
            </thead>
            <tbody>
              {riderCatalogRows.map((row) => (
                <tr key={row.id}><td>{row.id}</td><td>{row.user_id}</td><td>{row.zone_id || "-"}</td><td>{row.landline_phone || "-"}</td><td>{row.whatsapp_phone || "-"}</td><td>{row.vehicle_type}</td><td>{row.active ? "Sí" : "No"}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>}

      {section === "resultados" && <section className="panel">
        <h2>Catálogo de Estaciones</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>ID</th><th>Nombre</th><th>Zona</th><th>Teléfono fijo</th><th>WhatsApp</th><th>Activo</th></tr>
            </thead>
            <tbody>
              {stationCatalogRows.map((row) => (
                <tr key={row.id}><td>{row.id}</td><td>{row.name}</td><td>{row.zone_id}</td><td>{row.landline_phone || "-"}</td><td>{row.whatsapp_phone || "-"}</td><td>{row.active ? "Sí" : "No"}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>}
    </main>
  );
}

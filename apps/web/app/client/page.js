"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ClientPortalPage() {
  const [section, setSection] = useState("acceso");
  const [token, setToken] = useState("");
  const [registerName, setRegisterName] = useState("Nuevo Cliente");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerMsg, setRegisterMsg] = useState("");
  const [services, setServices] = useState([]);
  const [stations, setStations] = useState([]);
  const [originProfiles, setOriginProfiles] = useState([]);
  const [destinationProfiles, setDestinationProfiles] = useState([]);
  const [states, setStates] = useState([]);
  const [municipalities, setMunicipalities] = useState([]);
  const [postalCodes, setPostalCodes] = useState([]);
  const [colonies, setColonies] = useState([]);
  const [customerName, setCustomerName] = useState("Cliente Origen");
  const [destinationName, setDestinationName] = useState("Cliente Destino");
  const [originClientId, setOriginClientId] = useState("");
  const [destinationClientId, setDestinationClientId] = useState("");
  const [originWantsInvoice, setOriginWantsInvoice] = useState(false);
  const [serviceId, setServiceId] = useState("");
  const [stationId, setStationId] = useState("");
  const [newClientName, setNewClientName] = useState("");
  const [newClientKind, setNewClientKind] = useState("origin");
  const [stateCode, setStateCode] = useState("");
  const [municipalityCode, setMunicipalityCode] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [colonyId, setColonyId] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [landlinePhone, setLandlinePhone] = useState("");
  const [whatsappPhone, setWhatsappPhone] = useState("");
  const [createPortalAccess, setCreatePortalAccess] = useState(true);
  const [portalEmail, setPortalEmail] = useState("");
  const [portalPassword, setPortalPassword] = useState("");
  const [guideResult, setGuideResult] = useState(null);
  const [deliveryId, setDeliveryId] = useState("");
  const [sentGuides, setSentGuides] = useState([]);
  const [receivedGuides, setReceivedGuides] = useState([]);
  const [msg, setMsg] = useState("");
  const [geoLoading, setGeoLoading] = useState(false);

  const headers = useMemo(
    () => ({ Authorization: `Bearer ${token}`, "Content-Type": "application/json" }),
    [token]
  );

  useEffect(() => {
    const saved = localStorage.getItem("m24_token") || "";
    setToken(saved);
    const email = localStorage.getItem("m24_email") || "";
    if (email) setRegisterEmail(email);
  }, []);

  useEffect(() => {
    if (!token) {
      setStates([]);
      setMunicipalities([]);
      setPostalCodes([]);
      setColonies([]);
      setStateCode("");
      setMunicipalityCode("");
      setPostalCode("");
      setColonyId("");
      return;
    }
    loadGeoStates();
  }, [token]);

  async function registerAndLoginClient(e) {
    e.preventDefault();
    if (!registerEmail || !registerPassword || !registerName) {
      setRegisterMsg("Completa nombre, email y password.");
      return;
    }
    setRegisterMsg("Procesando registro...");

    try {
      const registerRes = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: registerEmail,
          full_name: registerName,
          password: registerPassword,
          role: "client",
        }),
      });
      if (!registerRes.ok && registerRes.status !== 409) {
        const err = await registerRes.text();
        setRegisterMsg(`Registro fallido: ${err}`);
        return;
      }

      const loginRes = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: registerEmail, password: registerPassword }),
      });
      if (!loginRes.ok) {
        const err = await loginRes.text();
        setRegisterMsg(`Login fallido: ${err}`);
        return;
      }

      const data = await loginRes.json();
      setToken(data.access_token);
      localStorage.setItem("m24_token", data.access_token);
      localStorage.setItem("m24_role", "client");
      localStorage.setItem("m24_email", registerEmail);
      setRegisterMsg("Cuenta lista. Sesion iniciada como cliente.");
      setMsg("Token de cliente listo. Ahora carga catalogos.");
    } catch (error) {
      setRegisterMsg(`Error: ${error.message}`);
    }
  }

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
      await Promise.all([loadProfiles(), loadGeoStates(), loadShipments()]);
      setMsg("Catalogos y clientes cargados.");
    } catch (error) {
      setMsg(`Error catalogos: ${error.message}`);
    }
  }

  async function loadProfiles() {
    const [origRes, destRes] = await Promise.all([
      fetch(`${API_BASE}/api/v1/clients/profiles?client_kind=origin`, { headers }),
      fetch(`${API_BASE}/api/v1/clients/profiles?client_kind=destination`, { headers }),
    ]);
    if (origRes.ok) {
      const rows = await origRes.json();
      setOriginProfiles(rows);
      if (!originClientId && rows.length) {
        setOriginClientId(rows[0].id);
        setCustomerName(rows[0].display_name);
        setOriginWantsInvoice(Boolean(rows[0].wants_invoice));
      }
    }
    if (destRes.ok) {
      const rows = await destRes.json();
      setDestinationProfiles(rows);
      if (!destinationClientId && rows.length) {
        setDestinationClientId(rows[0].id);
        setDestinationName(rows[0].display_name);
      }
    }
  }

  async function loadGeoStates() {
    setGeoLoading(true);
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/states`, { headers });
    if (!res.ok) {
      setGeoLoading(false);
      setMsg("No se pudo cargar Estados. Verifica token o sincronizacion geo.");
      return;
    }
    const rows = await res.json();
    setStates(rows);
    if (!stateCode && rows.length) setStateCode(rows[0].code);
    setGeoLoading(false);
  }

  async function loadMunicipalities(code) {
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
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/postal-codes?municipality_code=${encodeURIComponent(code)}`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    setPostalCodes(rows);
    setPostalCode(rows.length ? rows[0].code : "");
    setColonies([]);
    setColonyId("");
  }

  async function loadColonies(state, municipality, postal) {
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

  async function loadShipments() {
    const res = await fetch(`${API_BASE}/api/v1/clients/shipments/my`, { headers });
    if (!res.ok) return;
    const data = await res.json();
    setSentGuides(data.sent || []);
    setReceivedGuides(data.received || []);
  }

  async function createClientProfile(e) {
    e.preventDefault();
    if (!newClientName || !stateCode || !municipalityCode || !postalCode || !colonyId) {
      setMsg("Completa nombre, estado, municipio, CP y colonia del cliente.");
      return;
    }
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
      wants_invoice: originWantsInvoice,
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
    setMsg("Cliente registrado correctamente.");
    setNewClientName("");
    setAddressLine("");
    setLandlinePhone("");
    setWhatsappPhone("");
    setColonyId("");
    setPortalEmail("");
    setPortalPassword("");
    await loadProfiles();
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
        body: JSON.stringify({
          customer_name: customerName,
          destination_name: destinationName,
          origin_client_id: originClientId || null,
          destination_client_id: destinationClientId || null,
          origin_wants_invoice: originWantsInvoice,
          service_id: serviceId,
          station_id: stationId,
        }),
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
      await loadShipments();
    } catch (error) {
      setMsg(`Error creando guia: ${error.message}`);
    }
  }

  function onSelectOriginProfile(profileId) {
    setOriginClientId(profileId);
    const profile = originProfiles.find((item) => item.id === profileId);
    if (profile) {
      setCustomerName(profile.display_name);
      setOriginWantsInvoice(Boolean(profile.wants_invoice));
    }
  }

  function onSelectDestinationProfile(profileId) {
    setDestinationClientId(profileId);
    const profile = destinationProfiles.find((item) => item.id === profileId);
    if (profile) setDestinationName(profile.display_name);
  }

  function profileLabel(item) {
    return `${item.display_name} | Fijo: ${item.landline_phone || "-"} | WhatsApp: ${item.whatsapp_phone || "-"}`;
  }

  function stationLabel(item) {
    return `${item.name} | Fijo: ${item.landline_phone || "-"} | WhatsApp: ${item.whatsapp_phone || "-"}`;
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <img className="brand-logo" src="/brand/icon.svg" alt="Icono Mande24" />
          <div className="brand-copy">
            <h2>Portal Cliente</h2>
            <p className="brand-slogan">Registro, guias y seguimiento en una sola vista.</p>
          </div>
        </div>
        <nav className="nav-pills">
          <a className="nav-link" href="/">Inicio</a>
          <a className="nav-link" href="/servicios">Servicios</a>
          <a className="nav-link" href="/cobertura">Cobertura</a>
          <a className="nav-link" href="/noticias">Noticias</a>
          <a className="nav-link" href="/nosotros">Nosotros</a>
          <a className="nav-link" href="/contacto">Contacto</a>
          <a className="nav-link" href="/auth">Portal Auth</a>
          <a className="nav-link active" href="/client">Portal Cliente</a>
          <a className="nav-link" href="/rider">Portal Rider</a>
          <a className="nav-link" href="/station">Portal Estacion</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Portal Cliente</span>
      <h1>Gestion de Clientes y Guias</h1>
      <p className="hero-note">Registra clientes de origen y destino con direccion validada, define facturacion y opera guias con trazabilidad de envios enviados y recibidos.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner portal cliente" />

      <section className="panel">
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Captura de clientes y guias" />
            <div>
              <h3>Captura Estructurada</h3>
              <p className="hero-note">Completa direcciones con cascada geografia y crea guias con menos errores de captura.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-map.svg" alt="Cobertura por zonas de entrega" />
            <div>
              <h3>Envios con Contexto</h3>
              <p className="hero-note">Opera envios por zonas de cobertura para mejorar promesas de entrega y servicio.</p>
            </div>
          </article>
        </div>
      </section>

      <nav className="section-nav">
        <button className={section === "acceso" ? "section-link active" : "section-link"} onClick={() => setSection("acceso")}>Acceso</button>
        <button className={section === "catalogos" ? "section-link active" : "section-link"} onClick={() => setSection("catalogos")}>Token y Catalogos</button>
        <button className={section === "clientes" ? "section-link active" : "section-link"} onClick={() => setSection("clientes")}>Alta Cliente</button>
        <button className={section === "guias" ? "section-link active" : "section-link"} onClick={() => setSection("guias")}>Guias</button>
        <button className={section === "envios" ? "section-link active" : "section-link"} onClick={() => setSection("envios")}>Envios</button>
      </nav>

      {section === "acceso" && <section className="panel">
        <h2>Acceso para nuevos clientes</h2>
        <p className="field-hint">Crea tu cuenta desde esta seccion para ingresar al portal sin pasos adicionales.</p>
      </section>}

      {section === "acceso" && <section className="panel">
        <h2>Registro rapido de cuenta</h2>
        <p className="field-hint">Completa estos datos para activar tu acceso y autenticarte automaticamente.</p>
        <form className="form-grid" onSubmit={registerAndLoginClient}>
          <label>
            Nombre completo
            <input value={registerName} onChange={(e) => setRegisterName(e.target.value)} required />
          </label>
          <label>
            Email
            <input type="email" value={registerEmail} onChange={(e) => setRegisterEmail(e.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={registerPassword} onChange={(e) => setRegisterPassword(e.target.value)} required minLength={8} />
          </label>
          <button className="btn btn-primary" type="submit">Crear cuenta cliente</button>
        </form>
        <p className={`status-line ${registerMsg.includes("fallido") || registerMsg.includes("Error") ? "warn" : "ok"}`}>{registerMsg}</p>
      </section>}

      {section === "catalogos" && <section className="panel">
        <h2>Paso 1: Token y Catalogos</h2>
        <label>
          Token Bearer
          <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
        </label>
        <p className="field-hint">Si no cuentas con token, ingresa primero al portal `Auth` para autenticarte.</p>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={() => localStorage.setItem("m24_token", token)}>Guardar token</button>
          <button className="btn btn-primary" onClick={loadCatalogs}>Cargar catalogos</button>
        </div>
      </section>}

      {section === "clientes" && <section className="panel">
        <h2>Paso 2: Alta de Cliente</h2>
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
            <select value={stateCode} onChange={(e) => setStateCode(e.target.value)} disabled={!token || geoLoading || states.length === 0}>
              <option value="">{geoLoading ? "Cargando estados..." : (!token ? "Captura token primero" : "Selecciona estado")}</option>
              {states.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Municipio
            <select value={municipalityCode} onChange={(e) => setMunicipalityCode(e.target.value)} disabled={!token || municipalities.length === 0}>
              <option value="">{!token ? "Captura token primero" : "Selecciona municipio"}</option>
              {municipalities.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Codigo postal
            <select value={postalCode} onChange={(e) => setPostalCode(e.target.value)} disabled={!token || postalCodes.length === 0}>
              <option value="">{!token ? "Captura token primero" : "Selecciona codigo postal"}</option>
              {postalCodes.map((item) => <option key={item.code} value={item.code}>{item.code}</option>)}
            </select>
          </label>
          <label>
            Colonia
            <select value={colonyId} onChange={(e) => setColonyId(e.target.value)} disabled={!token || colonies.length === 0}>
              <option value="">Selecciona</option>
              {colonies.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Calle y numero
            <input value={addressLine} onChange={(e) => setAddressLine(e.target.value)} />
          </label>
          <label>
            Telefono fijo
            <input value={landlinePhone} onChange={(e) => setLandlinePhone(e.target.value)} />
          </label>
          <label>
            WhatsApp
            <input value={whatsappPhone} onChange={(e) => setWhatsappPhone(e.target.value)} />
          </label>
          <label>
            Facturar servicios (solo origen)
            <select value={originWantsInvoice ? "true" : "false"} onChange={(e) => setOriginWantsInvoice(e.target.value === "true")}>
              <option value="true">Si</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            Crear acceso portal/PWA destino
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

      {section === "guias" && <section className="panel">
        <h2>Paso 3: Crear Guia</h2>
        <form className="form-grid" onSubmit={createGuide}>
          <label>
            Cliente origen
            <select value={originClientId} onChange={(e) => onSelectOriginProfile(e.target.value)}>
              <option value="">Selecciona</option>
              {originProfiles.map((item) => <option key={item.id} value={item.id}>{profileLabel(item)}</option>)}
            </select>
          </label>
          <label>
            Cliente destino
            <select value={destinationClientId} onChange={(e) => onSelectDestinationProfile(e.target.value)}>
              <option value="">Selecciona</option>
              {destinationProfiles.map((item) => <option key={item.id} value={item.id}>{profileLabel(item)}</option>)}
            </select>
          </label>
          <label>
            Facturar servicio origen
            <select value={originWantsInvoice ? "true" : "false"} onChange={(e) => setOriginWantsInvoice(e.target.value === "true")}>
              <option value="true">Si</option>
              <option value="false">No</option>
            </select>
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
                <option key={item.id} value={item.id}>{stationLabel(item)}</option>
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
            {deliveryId && <p className="field-hint">Siguiente paso: abre `Rider` y utiliza este Delivery ID para actualizar etapas.</p>}
          </div>
        )}
        <p className={`status-line ${msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
      </section>}

      {section === "envios" && <section className="panel">
        <h2>Historial de Envios</h2>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={loadShipments}>Actualizar envios</button>
        </div>
        <h3>Enviados</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Guia</th><th>Origen</th><th>Destino</th><th>Monto</th></tr></thead>
            <tbody>
              {sentGuides.map((item) => (
                <tr key={`sent-${item.guide_code}`}><td>{item.guide_code}</td><td>{item.customer_name}</td><td>{item.destination_name}</td><td>{item.sale_amount} {item.currency}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3>Recibidos</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Guia</th><th>Origen</th><th>Destino</th><th>Monto</th></tr></thead>
            <tbody>
              {receivedGuides.map((item) => (
                <tr key={`recv-${item.guide_code}`}><td>{item.guide_code}</td><td>{item.customer_name}</td><td>{item.destination_name}</td><td>{item.sale_amount} {item.currency}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>}
    </main>
  );
}

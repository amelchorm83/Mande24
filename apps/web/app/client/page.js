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
  const [originLandlinePhone, setOriginLandlinePhone] = useState("");
  const [originWhatsappPhone, setOriginWhatsappPhone] = useState("");
  const [originEmail, setOriginEmail] = useState("");
  const [originStateCode, setOriginStateCode] = useState("");
  const [originMunicipalities, setOriginMunicipalities] = useState([]);
  const [originMunicipalityCode, setOriginMunicipalityCode] = useState("");
  const [originPostalCodes, setOriginPostalCodes] = useState([]);
  const [originPostalCode, setOriginPostalCode] = useState("");
  const [originColonies, setOriginColonies] = useState([]);
  const [originColonyId, setOriginColonyId] = useState("");
  const [originAddressLine, setOriginAddressLine] = useState("");
  const [destinationLandlinePhone, setDestinationLandlinePhone] = useState("");
  const [destinationWhatsappPhone, setDestinationWhatsappPhone] = useState("");
  const [destinationEmail, setDestinationEmail] = useState("");
  const [destinationStateCode, setDestinationStateCode] = useState("");
  const [destinationMunicipalities, setDestinationMunicipalities] = useState([]);
  const [destinationMunicipalityCode, setDestinationMunicipalityCode] = useState("");
  const [destinationPostalCodes, setDestinationPostalCodes] = useState([]);
  const [destinationPostalCode, setDestinationPostalCode] = useState("");
  const [destinationColonies, setDestinationColonies] = useState([]);
  const [destinationColonyId, setDestinationColonyId] = useState("");
  const [destinationAddressLine, setDestinationAddressLine] = useState("");
  const [originZoneSuggest, setOriginZoneSuggest] = useState("-");
  const [originStationSuggest, setOriginStationSuggest] = useState("-");
  const [destinationZoneSuggest, setDestinationZoneSuggest] = useState("-");
  const [destinationStationSuggest, setDestinationStationSuggest] = useState("-");
  const [requesterRole, setRequesterRole] = useState("origin");
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
  const [routeLegRows, setRouteLegRows] = useState([]);
  const [trackingGuideCode, setTrackingGuideCode] = useState("");
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
    if (email) {
      setRegisterEmail(email);
      setOriginEmail(email);
    }
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
      setOriginStateCode("");
      setOriginMunicipalityCode("");
      setOriginPostalCode("");
      setOriginColonyId("");
      setDestinationStateCode("");
      setDestinationMunicipalityCode("");
      setDestinationPostalCode("");
      setDestinationColonyId("");
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
      setRegisterMsg("Cuenta lista. Sesión iniciada como cliente.");
      setMsg("Token de cliente listo. Ahora carga catálogos.");
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

  useEffect(() => {
    if (!token || !originStateCode) return;
    loadGuideMunicipalities("origin", originStateCode);
  }, [token, originStateCode]);

  useEffect(() => {
    if (!token || !originMunicipalityCode) return;
    loadGuidePostalCodes("origin", originMunicipalityCode);
  }, [token, originMunicipalityCode]);

  useEffect(() => {
    if (!token || !originStateCode || !originMunicipalityCode || !originPostalCode) return;
    loadGuideColonies("origin", originStateCode, originMunicipalityCode, originPostalCode);
  }, [token, originStateCode, originMunicipalityCode, originPostalCode]);

  useEffect(() => {
    if (!token || !destinationStateCode) return;
    loadGuideMunicipalities("destination", destinationStateCode);
  }, [token, destinationStateCode]);

  useEffect(() => {
    if (!token || !destinationMunicipalityCode) return;
    loadGuidePostalCodes("destination", destinationMunicipalityCode);
  }, [token, destinationMunicipalityCode]);

  useEffect(() => {
    if (!token || !destinationStateCode || !destinationMunicipalityCode || !destinationPostalCode) return;
    loadGuideColonies("destination", destinationStateCode, destinationMunicipalityCode, destinationPostalCode);
  }, [token, destinationStateCode, destinationMunicipalityCode, destinationPostalCode]);

  useEffect(() => {
    if (!token || !originStateCode || !originMunicipalityCode || !originPostalCode) return;
    resolveCoverage("origin", originStateCode, originMunicipalityCode, originPostalCode, originColonyId);
  }, [token, originStateCode, originMunicipalityCode, originPostalCode, originColonyId]);

  useEffect(() => {
    if (!token || !destinationStateCode || !destinationMunicipalityCode || !destinationPostalCode) return;
    resolveCoverage("destination", destinationStateCode, destinationMunicipalityCode, destinationPostalCode, destinationColonyId);
  }, [token, destinationStateCode, destinationMunicipalityCode, destinationPostalCode, destinationColonyId]);

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
        setMsg("No se pudieron cargar catálogos. Revisa tu token/rol.");
        return;
      }
      const svcData = await svcRes.json();
      const stData = await stRes.json();
      setServices(svcData);
      setStations(stData);
      if (svcData.length && !serviceId) setServiceId(svcData[0].id);
      if (stData.length && !stationId) setStationId(stData[0].id);
      await Promise.all([loadProfiles(), loadGeoStates(), loadShipments()]);
      setMsg("Catálogos y clientes cargados.");
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
        setOriginLandlinePhone(rows[0].landline_phone || "");
        setOriginWhatsappPhone(rows[0].whatsapp_phone || "");
        setOriginStateCode(rows[0].state_code || "");
        setOriginMunicipalityCode(rows[0].municipality_code || "");
        setOriginPostalCode(rows[0].postal_code || "");
        setOriginColonyId(rows[0].colony_id || "");
        setOriginAddressLine(rows[0].address_line || "");
      }
    }
    if (destRes.ok) {
      const rows = await destRes.json();
      setDestinationProfiles(rows);
      if (!destinationClientId && rows.length) {
        setDestinationClientId(rows[0].id);
        setDestinationName(rows[0].display_name);
        setDestinationLandlinePhone(rows[0].landline_phone || "");
        setDestinationWhatsappPhone(rows[0].whatsapp_phone || "");
        setDestinationStateCode(rows[0].state_code || "");
        setDestinationMunicipalityCode(rows[0].municipality_code || "");
        setDestinationPostalCode(rows[0].postal_code || "");
        setDestinationColonyId(rows[0].colony_id || "");
        setDestinationAddressLine(rows[0].address_line || "");
      }
    }
  }

  async function loadGeoStates() {
    setGeoLoading(true);
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/states`, { headers });
    if (!res.ok) {
      setGeoLoading(false);
      setMsg("No se pudo cargar Estados. Verifica token o sincronización geo.");
      return;
    }
    const rows = await res.json();
    setStates(rows);
    if (!stateCode && rows.length) setStateCode(rows[0].code);
    if (!originStateCode && rows.length) setOriginStateCode(rows[0].code);
    if (!destinationStateCode && rows.length) setDestinationStateCode(rows[0].code);
    setGeoLoading(false);
  }

  async function loadGuideMunicipalities(side, code) {
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/municipalities?state_code=${encodeURIComponent(code)}`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    if (side === "origin") {
      setOriginMunicipalities(rows);
      setOriginMunicipalityCode(rows.length ? rows[0].code : "");
      setOriginPostalCodes([]);
      setOriginPostalCode("");
      setOriginColonies([]);
      setOriginColonyId("");
      return;
    }
    setDestinationMunicipalities(rows);
    setDestinationMunicipalityCode(rows.length ? rows[0].code : "");
    setDestinationPostalCodes([]);
    setDestinationPostalCode("");
    setDestinationColonies([]);
    setDestinationColonyId("");
  }

  async function loadGuidePostalCodes(side, code) {
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/postal-codes?municipality_code=${encodeURIComponent(code)}`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    if (side === "origin") {
      setOriginPostalCodes(rows);
      setOriginPostalCode(rows.length ? rows[0].code : "");
      setOriginColonies([]);
      setOriginColonyId("");
      return;
    }
    setDestinationPostalCodes(rows);
    setDestinationPostalCode(rows.length ? rows[0].code : "");
    setDestinationColonies([]);
    setDestinationColonyId("");
  }

  async function loadGuideColonies(side, state, municipality, postal) {
    const q = new URLSearchParams({
      state_code: state,
      municipality_code: municipality,
      postal_code: postal,
    });
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/colonies?${q.toString()}`, { headers });
    if (!res.ok) return;
    const rows = await res.json();
    if (side === "origin") {
      setOriginColonies(rows);
      setOriginColonyId(rows.length ? rows[0].id : "");
      return;
    }
    setDestinationColonies(rows);
    setDestinationColonyId(rows.length ? rows[0].id : "");
  }

  async function resolveCoverage(side, state, municipality, postal, colony) {
    const q = new URLSearchParams({
      state_code: state,
      municipality_code: municipality,
      postal_code: postal,
      colony_id: colony || "",
    });
    const res = await fetch(`${API_BASE}/api/v1/clients/geo/service-coverage?${q.toString()}`, { headers });
    if (!res.ok) return;
    const data = await res.json();

    if (side === "origin") {
      setOriginZoneSuggest(data.zone_name || "-");
      setOriginStationSuggest(data.station_name || "-");
      if (!stationId && data.station_id) setStationId(data.station_id);
      return;
    }

    setDestinationZoneSuggest(data.zone_name || "-");
    setDestinationStationSuggest(data.station_name || "-");
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
      setMsg("Selecciona servicio y estación.");
      return;
    }
    if (
      !originWhatsappPhone || !originEmail || !originStateCode || !originMunicipalityCode || !originPostalCode || !originColonyId || !originAddressLine ||
      !destinationWhatsappPhone || !destinationEmail || !destinationStateCode || !destinationMunicipalityCode || !destinationPostalCode || !destinationColonyId || !destinationAddressLine
    ) {
      setMsg("Completa WhatsApp, email y direccion georeferenciada de origen y destino.");
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
          origin_landline_phone: originLandlinePhone || null,
          origin_whatsapp_phone: originWhatsappPhone,
          origin_email: originEmail,
          origin_state_code: originStateCode,
          origin_municipality_code: originMunicipalityCode,
          origin_postal_code: originPostalCode,
          origin_colony_id: originColonyId,
          origin_address_line: originAddressLine,
          destination_landline_phone: destinationLandlinePhone || null,
          destination_whatsapp_phone: destinationWhatsappPhone,
          destination_email: destinationEmail,
          destination_state_code: destinationStateCode,
          destination_municipality_code: destinationMunicipalityCode,
          destination_postal_code: destinationPostalCode,
          destination_colony_id: destinationColonyId,
          destination_address_line: destinationAddressLine,
          requester_role: requesterRole,
          origin_wants_invoice: originWantsInvoice,
          service_id: serviceId,
          station_id: stationId,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error creando guía: ${JSON.stringify(data)}`);
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
      setTrackingGuideCode(data.guide_code || "");
      setMsg("Guía creada correctamente.");
      await loadRouteLegs(data.guide_code);
      await loadShipments();
    } catch (error) {
      setMsg(`Error creando guía: ${error.message}`);
    }
  }

  async function loadRouteLegs(guideCodeInput = trackingGuideCode) {
    const safeGuideCode = (guideCodeInput || "").trim().toUpperCase();
    if (!safeGuideCode) {
      setMsg("Ingresa código de guía para consultar tramos.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/guides/${encodeURIComponent(safeGuideCode)}/route-legs`, { headers });
      const data = await res.json();
      if (!res.ok) {
        setMsg(`Error consultando ruta: ${JSON.stringify(data)}`);
        return;
      }
      setRouteLegRows(data);
      setMsg(`Ruta cargada para ${safeGuideCode}: ${data.length} tramos.`);
    } catch (error) {
      setMsg(`Error consultando ruta: ${error.message}`);
    }
  }

  function onSelectOriginProfile(profileId) {
    setOriginClientId(profileId);
    const profile = originProfiles.find((item) => item.id === profileId);
    if (profile) {
      setCustomerName(profile.display_name);
      setOriginWantsInvoice(Boolean(profile.wants_invoice));
      setOriginLandlinePhone(profile.landline_phone || "");
      setOriginWhatsappPhone(profile.whatsapp_phone || "");
      setOriginStateCode(profile.state_code || "");
      setOriginMunicipalityCode(profile.municipality_code || "");
      setOriginPostalCode(profile.postal_code || "");
      setOriginColonyId(profile.colony_id || "");
      setOriginAddressLine(profile.address_line || "");
    }
  }

  function onSelectDestinationProfile(profileId) {
    setDestinationClientId(profileId);
    const profile = destinationProfiles.find((item) => item.id === profileId);
    if (profile) {
      setDestinationName(profile.display_name);
      setDestinationLandlinePhone(profile.landline_phone || "");
      setDestinationWhatsappPhone(profile.whatsapp_phone || "");
      setDestinationStateCode(profile.state_code || "");
      setDestinationMunicipalityCode(profile.municipality_code || "");
      setDestinationPostalCode(profile.postal_code || "");
      setDestinationColonyId(profile.colony_id || "");
      setDestinationAddressLine(profile.address_line || "");
    }
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
            <p className="brand-slogan">Registro, guías y seguimiento en una sola vista.</p>
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
          <a className="nav-link" href="/station">Portal Estación</a>
        
          <a className="nav-link" href="/cotizador">Cotizador</a>
          <a className="nav-link" href="/niveles-servicio">Niveles de Servicio</a>
          <a className="nav-link" href="/industrias">Industrias</a></nav>
      </header>

      <span className="badge">Portal Cliente</span>
      <h1>Gestión de Clientes y Guías</h1>
      <p className="hero-note">Registra clientes de origen y destino con dirección validada, define facturación y opera guías con trazabilidad de envíos enviados y recibidos.</p>
      <img className="hero-banner" src="/brand/banner.svg" alt="Banner portal cliente" />

      <section className="panel">
        <div className="media-grid">
          <article className="media-card">
            <img src="/brand/photo-hub.svg" alt="Captura de clientes y guías" />
            <div>
              <h3>Captura Estructurada</h3>
              <p className="hero-note">Completa direcciones con cascada geografía y crea guías con menos errores de captura.</p>
            </div>
          </article>
          <article className="media-card">
            <img src="/brand/photo-map.svg" alt="Cobertura por zonas de entrega" />
            <div>
              <h3>Envíos con Contexto</h3>
              <p className="hero-note">Opera envíos por zonas de cobertura para mejorar promesas de entrega y servicio.</p>
            </div>
          </article>
        </div>
      </section>

      <nav className="section-nav">
        <button className={section === "acceso" ? "section-link active" : "section-link"} onClick={() => setSection("acceso")}>Acceso</button>
        <button className={section === "catalogos" ? "section-link active" : "section-link"} onClick={() => setSection("catalogos")}>Token y Catálogos</button>
        <button className={section === "clientes" ? "section-link active" : "section-link"} onClick={() => setSection("clientes")}>Alta Cliente</button>
        <button className={section === "guias" ? "section-link active" : "section-link"} onClick={() => setSection("guias")}>Guías</button>
        <button className={section === "envios" ? "section-link active" : "section-link"} onClick={() => setSection("envios")}>Envíos</button>
      </nav>

      {section === "acceso" && <section className="panel">
        <h2>Acceso para nuevos clientes</h2>
        <p className="field-hint">Crea tu cuenta desde esta sección para ingresar al portal sin pasos adicionales.</p>
      </section>}

      {section === "acceso" && <section className="panel">
        <h2>Registro rápido de cuenta</h2>
        <p className="field-hint">Completa estos datos para activar tu acceso y autenticarte automáticamente.</p>
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
        <h2>Paso 1: Token y Catálogos</h2>
        <label>
          Token Bearer
          <textarea value={token} onChange={(e) => setToken(e.target.value)} rows={4} className="mono-box" />
        </label>
        <p className="field-hint">Si no cuentas con token, ingresa primero al portal `Auth` para autenticarte.</p>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={() => localStorage.setItem("m24_token", token)}>Guardar token</button>
          <button className="btn btn-primary" onClick={loadCatalogs}>Cargar catálogos</button>
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
            Código postal
            <select value={postalCode} onChange={(e) => setPostalCode(e.target.value)} disabled={!token || postalCodes.length === 0}>
              <option value="">{!token ? "Captura token primero" : "Selecciona código postal"}</option>
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
            Facturar servicios (solo origen)
            <select value={originWantsInvoice ? "true" : "false"} onChange={(e) => setOriginWantsInvoice(e.target.value === "true")}>
              <option value="true">Sí</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            Crear acceso portal/PWA destino
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
                Password portal
                <input type="password" value={portalPassword} onChange={(e) => setPortalPassword(e.target.value)} required />
              </label>
            </>
          )}
          <button className="btn btn-primary" type="submit">Registrar cliente</button>
        </form>
      </section>}

      {section === "guias" && <section className="panel">
        <h2>Paso 3: Crear Guía</h2>
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
              <option value="true">Sí</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            Origen teléfono fijo (opcional)
            <input value={originLandlinePhone} onChange={(e) => setOriginLandlinePhone(e.target.value)} />
          </label>
          <label>
            Origen WhatsApp (obligatorio)
            <input value={originWhatsappPhone} onChange={(e) => setOriginWhatsappPhone(e.target.value)} required />
          </label>
          <label>
            Origen email (obligatorio)
            <input type="email" value={originEmail} onChange={(e) => setOriginEmail(e.target.value)} required />
          </label>
          <label>
            Origen estado
            <select value={originStateCode} onChange={(e) => setOriginStateCode(e.target.value)}>
              <option value="">Selecciona</option>
              {states.map((item) => <option key={`o-st-${item.code}`} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Origen municipio
            <select value={originMunicipalityCode} onChange={(e) => setOriginMunicipalityCode(e.target.value)}>
              <option value="">Selecciona</option>
              {originMunicipalities.map((item) => <option key={`o-mn-${item.code}`} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Origen código postal
            <select value={originPostalCode} onChange={(e) => setOriginPostalCode(e.target.value)}>
              <option value="">Selecciona</option>
              {originPostalCodes.map((item) => <option key={`o-cp-${item.code}`} value={item.code}>{item.code}</option>)}
            </select>
          </label>
          <label>
            Origen colonia
            <select value={originColonyId} onChange={(e) => setOriginColonyId(e.target.value)}>
              <option value="">Selecciona</option>
              {originColonies.map((item) => <option key={`o-col-${item.id}`} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Origen dirección (solo guía)
            <input value={originAddressLine} onChange={(e) => setOriginAddressLine(e.target.value)} required />
          </label>
          <label>
            Destino teléfono fijo (opcional)
            <input value={destinationLandlinePhone} onChange={(e) => setDestinationLandlinePhone(e.target.value)} />
          </label>
          <label>
            Destino WhatsApp (obligatorio)
            <input value={destinationWhatsappPhone} onChange={(e) => setDestinationWhatsappPhone(e.target.value)} required />
          </label>
          <label>
            Destino email (obligatorio)
            <input type="email" value={destinationEmail} onChange={(e) => setDestinationEmail(e.target.value)} required />
          </label>
          <label>
            Destino estado
            <select value={destinationStateCode} onChange={(e) => setDestinationStateCode(e.target.value)}>
              <option value="">Selecciona</option>
              {states.map((item) => <option key={`d-st-${item.code}`} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Destino municipio
            <select value={destinationMunicipalityCode} onChange={(e) => setDestinationMunicipalityCode(e.target.value)}>
              <option value="">Selecciona</option>
              {destinationMunicipalities.map((item) => <option key={`d-mn-${item.code}`} value={item.code}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Destino código postal
            <select value={destinationPostalCode} onChange={(e) => setDestinationPostalCode(e.target.value)}>
              <option value="">Selecciona</option>
              {destinationPostalCodes.map((item) => <option key={`d-cp-${item.code}`} value={item.code}>{item.code}</option>)}
            </select>
          </label>
          <label>
            Destino colonia
            <select value={destinationColonyId} onChange={(e) => setDestinationColonyId(e.target.value)}>
              <option value="">Selecciona</option>
              {destinationColonies.map((item) => <option key={`d-col-${item.id}`} value={item.id}>{item.name}</option>)}
            </select>
          </label>
          <label>
            Destino dirección (solo guía)
            <input value={destinationAddressLine} onChange={(e) => setDestinationAddressLine(e.target.value)} required />
          </label>
          <label>
            Solicitante del servicio
            <select value={requesterRole} onChange={(e) => setRequesterRole(e.target.value)}>
              <option value="origin">Cliente origen</option>
              <option value="destination">Cliente destino</option>
              <option value="external">Tercero / externo</option>
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
            Estación
            <select value={stationId} onChange={(e) => setStationId(e.target.value)}>
              <option value="">Selecciona</option>
              {stations.map((item) => (
                <option key={item.id} value={item.id}>{stationLabel(item)}</option>
              ))}
            </select>
          </label>
          <label>
            Zona sugerida origen
            <input value={originZoneSuggest} readOnly />
          </label>
          <label>
            Estación sugerida origen
            <input value={originStationSuggest} readOnly />
          </label>
          <label>
            Zona sugerida destino
            <input value={destinationZoneSuggest} readOnly />
          </label>
          <label>
            Estación sugerida destino
            <input value={destinationStationSuggest} readOnly />
          </label>
          <button className="btn btn-primary" type="submit">Crear guía</button>
        </form>

        {guideResult && (
          <div className="result-box">
            <p><strong>Guía:</strong> {guideResult.guide_code}</p>
            <p><strong>Venta:</strong> {guideResult.sale_amount} {guideResult.currency}</p>
            {deliveryId && <p><strong>Delivery ID:</strong> {deliveryId}</p>}
            {deliveryId && <p className="field-hint">Siguiente paso: abre `Rider` y utiliza este Delivery ID para actualizar etapas.</p>}
          </div>
        )}

        <h3>Tracking de ruta por tramos</h3>
        <div className="inline-actions">
          <input value={trackingGuideCode} onChange={(e) => setTrackingGuideCode(e.target.value)} placeholder="Código de guía" />
          <button className="btn btn-ghost" type="button" onClick={() => loadRouteLegs()}>Consultar tramos</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Seq</th><th>Tipo</th><th>Estado</th><th>Rider</th><th>Tarifa rider</th><th>Tarifa estación</th></tr></thead>
            <tbody>
              {routeLegRows.map((row) => (
                <tr key={row.id}>
                  <td>{row.sequence}</td><td>{row.leg_type}</td><td>{row.status}</td><td>{row.assigned_rider_id || "-"}</td><td>{row.rider_fee_amount} {row.currency}</td><td>{row.station_fee_amount} {row.currency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={`status-line ${msg.includes("Error") ? "warn" : "ok"}`}>{msg}</p>
      </section>}

      {section === "envios" && <section className="panel">
        <h2>Historial de Envíos</h2>
        <div className="inline-actions">
          <button className="btn btn-ghost" onClick={loadShipments}>Actualizar envíos</button>
        </div>
        <h3>Enviados</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Guía</th><th>Origen</th><th>Destino</th><th>Monto</th></tr></thead>
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
            <thead><tr><th>Guía</th><th>Origen</th><th>Destino</th><th>Monto</th></tr></thead>
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

import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import AuthPage from "../app/auth/page";
import ClientPortalPage from "../app/client/page";
import RiderPortalPage from "../app/rider/page";
import StationPortalPage from "../app/station/page";

beforeEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("portal interactions", () => {
  it("auth page switches to register mode", () => {
    render(<AuthPage />);

    fireEvent.click(screen.getByRole("button", { name: "Register + Login" }));

    expect(screen.getByText("Nombre completo")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crear y Entrar" })).toBeInTheDocument();
  });

  it("auth page stores token on successful login", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "token-123" }),
    });

    render(<AuthPage />);
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(localStorage.getItem("m24_token")).toBe("token-123");
    });

    expect(screen.getByText(/Autenticado\. Token guardado/)).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/login"),
      expect.objectContaining({ method: "POST" })
    );

    const [loginUrl, loginOptions] = fetchSpy.mock.calls[0];
    expect(String(loginUrl)).toContain("/api/v1/auth/login");
    expect(loginOptions.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(JSON.parse(loginOptions.body)).toEqual({
      email: "admin.ops@mande24.local",
      password: "Secret123",
    });
  });

  it("auth page register mode sends register then login with exact payloads", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "token-register" }),
      status: 200,
    });

    render(<AuthPage />);

    fireEvent.click(screen.getByRole("button", { name: "Register + Login" }));
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "new.user@mande24.local" } });
    fireEvent.change(screen.getByLabelText("Nombre completo"), { target: { value: "New User" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Secret123" } });
    fireEvent.change(screen.getByLabelText("Rol"), { target: { value: "station" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear y Entrar" }));

    await waitFor(() => {
      expect(localStorage.getItem("m24_token")).toBe("token-register");
    });

    expect(fetchSpy).toHaveBeenCalledTimes(2);

    const [registerUrl, registerOptions] = fetchSpy.mock.calls[0];
    expect(String(registerUrl)).toContain("/api/v1/auth/register");
    expect(registerOptions.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(JSON.parse(registerOptions.body)).toEqual({
      email: "new.user@mande24.local",
      full_name: "New User",
      password: "Secret123",
      role: "station",
    });

    const [loginUrl, loginOptions] = fetchSpy.mock.calls[1];
    expect(String(loginUrl)).toContain("/api/v1/auth/login");
    expect(loginOptions.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(JSON.parse(loginOptions.body)).toEqual({
      email: "new.user@mande24.local",
      password: "Secret123",
    });
  });

  it("client page warns when trying to load catalogs without token", () => {
    render(<ClientPortalPage />);

    fireEvent.click(screen.getByRole("button", { name: "Cargar catálogos" }));

    expect(screen.getByText("Necesitas token. Ve primero a /auth.")).toBeInTheDocument();
  });

  it("client page loads catalogs and creates guide with delivery id", async () => {
    localStorage.setItem("m24_token", "token-client");
    localStorage.setItem("m24_email", "client@test.local");

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (url, options) => {
      const requestUrl = String(url);

      if (requestUrl.includes("/api/v1/clients/geo/states")) {
        return { ok: true, json: async () => [{ code: "TAB", name: "Tabasco" }] };
      }

      if (requestUrl.includes("/api/v1/clients/geo/municipalities")) {
        return { ok: true, json: async () => [{ code: "CEN", name: "Centro" }] };
      }

      if (requestUrl.includes("/api/v1/clients/geo/postal-codes")) {
        return { ok: true, json: async () => [{ code: "86000" }] };
      }

      if (requestUrl.includes("/api/v1/clients/geo/colonies")) {
        return { ok: true, json: async () => [{ id: "COL-1", name: "Centro" }] };
      }

      if (requestUrl.includes("/api/v1/clients/geo/service-coverage")) {
        return { ok: true, json: async () => ({ zone_name: "Zona Centro", station_name: "Estacion Centro", station_id: "st-1" }) };
      }

      if (requestUrl.includes("/api/v1/clients/profiles?client_kind=origin")) {
        return {
          ok: true,
          json: async () => [{
            id: "orig-1",
            display_name: "Cliente Origen",
            wants_invoice: false,
            landline_phone: "",
            whatsapp_phone: "5511111111",
            state_code: "TAB",
            municipality_code: "CEN",
            postal_code: "86000",
            colony_id: "COL-1",
            address_line: "Calle 1",
          }],
        };
      }

      if (requestUrl.includes("/api/v1/clients/profiles?client_kind=destination")) {
        return {
          ok: true,
          json: async () => [{
            id: "dest-1",
            display_name: "Cliente Destino",
            landline_phone: "",
            whatsapp_phone: "5522222222",
            state_code: "TAB",
            municipality_code: "CEN",
            postal_code: "86000",
            colony_id: "COL-1",
            address_line: "Calle 2",
          }],
        };
      }

      if (requestUrl.includes("/api/v1/clients/shipments/my")) {
        return { ok: true, json: async () => ({ sent: [], received: [] }) };
      }

      if (requestUrl.includes("/api/v1/catalogs/services")) {
        return {
          ok: true,
          json: async () => [{ id: "svc-1", name: "Mensajeria" }],
        };
      }

      if (requestUrl.includes("/api/v1/catalogs/stations")) {
        return {
          ok: true,
          json: async () => [{ id: "st-1", name: "Estacion Centro" }],
        };
      }

      if (requestUrl.endsWith("/api/v1/guides") && options?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ guide_code: "M24-20260308-ABC123", sale_amount: 120, currency: "MXN" }),
        };
      }

      if (requestUrl.includes("/api/v1/guides/M24-20260308-ABC123/deliveries")) {
        return {
          ok: true,
          json: async () => [{ delivery_id: "deliv-001" }],
        };
      }

      return { ok: false, json: async () => ({}) };
    });

    render(<ClientPortalPage />);

    fireEvent.click(screen.getByRole("button", { name: "Cargar catálogos" }));

    await waitFor(() => {
      expect(screen.getByText("Catalogos cargados.")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Origen email (obligatorio)"), { target: { value: "origen@test.local" } });
    fireEvent.change(screen.getByLabelText("Destino email (obligatorio)"), { target: { value: "destino@test.local" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear guía" }));

    await waitFor(() => {
      expect(screen.getByText("Guia creada correctamente.")).toBeInTheDocument();
    });

    expect(screen.getByText(/Delivery ID:/)).toBeInTheDocument();
    expect(screen.getByText("deliv-001")).toBeInTheDocument();

    const guideCall = fetchSpy.mock.calls.find(
      ([url, options]) => String(url).endsWith("/api/v1/guides") && options?.method === "POST"
    );
    expect(guideCall).toBeTruthy();

    const [, guideOptions] = guideCall;
    expect(guideOptions.headers).toMatchObject({
      Authorization: "Bearer token-client",
      "Content-Type": "application/json",
    });
    const body = JSON.parse(guideOptions.body);
    expect(body.service_id).toBe("svc-1");
    expect(body.station_id).toBe("st-1");
    expect(body.origin_whatsapp_phone).toBeTruthy();
    expect(body.origin_email).toBe("origen@test.local");
    expect(body.origin_state_code).toBeTruthy();
    expect(body.origin_municipality_code).toBeTruthy();
    expect(body.origin_postal_code).toBeTruthy();
    expect(body.origin_colony_id).toBeTruthy();
    expect(body.origin_address_line).toBeTruthy();
    expect(body.destination_whatsapp_phone).toBeTruthy();
    expect(body.destination_email).toBe("destino@test.local");
    expect(body.destination_state_code).toBeTruthy();
    expect(body.destination_municipality_code).toBeTruthy();
    expect(body.destination_postal_code).toBeTruthy();
    expect(body.destination_colony_id).toBeTruthy();
    expect(body.destination_address_line).toBeTruthy();
  });

  it("rider page validates empty delivery id", () => {
    render(<RiderPortalPage />);

    fireEvent.click(screen.getByRole("button", { name: "Actualizar etapa" }));

    expect(screen.getByText("Ingresa delivery_id")).toBeInTheDocument();
  });

  it("rider page updates stage successfully", async () => {
    localStorage.setItem("m24_token", "token-rider");

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ stage: "delivered" }),
    });

    render(<RiderPortalPage />);

    fireEvent.change(screen.getByLabelText("Delivery ID"), { target: { value: "deliv-007" } });
    fireEvent.change(screen.getByLabelText("Nueva etapa"), { target: { value: "delivered" } });
    fireEvent.click(screen.getByLabelText("Evidencia"));
    fireEvent.click(screen.getByLabelText("Firma"));
    fireEvent.click(screen.getByRole("button", { name: "Actualizar etapa" }));

    await waitFor(() => {
      expect(screen.getByText("Entrega actualizada: delivered")).toBeInTheDocument();
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/guides/deliveries/deliv-007/stage"),
      expect.objectContaining({ method: "PATCH" })
    );

    const [calledUrl, calledOptions] = fetchSpy.mock.calls[0];
    expect(String(calledUrl)).toContain("/api/v1/guides/deliveries/deliv-007/stage");
    expect(calledOptions.headers).toMatchObject({
      Authorization: "Bearer token-rider",
      "Content-Type": "application/json",
    });
    expect(JSON.parse(calledOptions.body)).toEqual({
      stage: "delivered",
      has_evidence: true,
      has_signature: true,
    });
  });

  it("station page shows message when commission endpoints fail", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: false });

    render(<StationPortalPage />);
    fireEvent.click(screen.getByRole("button", { name: "Cargar comisiones" }));

    await waitFor(() => {
      expect(screen.getByText("No se pudieron obtener comisiones. Revisa rol/token.")).toBeInTheDocument();
    });
  });
});

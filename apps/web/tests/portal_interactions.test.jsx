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

    fireEvent.click(screen.getByRole("button", { name: "Cargar catalogos" }));

    expect(screen.getByText("Necesitas token. Ve primero a /auth.")).toBeInTheDocument();
  });

  it("client page loads catalogs and creates guide with delivery id", async () => {
    localStorage.setItem("m24_token", "token-client");

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(async (url, options) => {
      const requestUrl = String(url);

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

    fireEvent.click(screen.getByRole("button", { name: "Cargar catalogos" }));

    await waitFor(() => {
      expect(screen.getByText("Catalogos cargados.")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Crear guia" }));

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
    expect(JSON.parse(guideOptions.body)).toEqual({
      customer_name: "Cliente Portal",
      destination_name: "Destino Portal",
      requester_role: "origin",
      service_id: "svc-1",
      station_id: "st-1",
    });
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

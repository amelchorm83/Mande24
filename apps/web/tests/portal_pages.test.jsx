import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import AuthPage from "../app/auth/page";
import ClientPortalPage from "../app/client/page";
import RiderPortalPage from "../app/rider/page";
import StationPortalPage from "../app/station/page";

describe("portal pages", () => {
  it("renders auth portal key content", () => {
    const html = renderToStaticMarkup(<AuthPage />);

    expect(html).toContain("Portal Auth");
    expect(html).toContain("Acceso y Token");
    expect(html).toContain("/client");
    expect(html).toContain("Roles permitidos");
  });

  it("renders client portal key content", () => {
    const html = renderToStaticMarkup(<ClientPortalPage />);

    expect(html).toContain("Portal Cliente");
    expect(html).toContain("Crear Guia Operativa");
    expect(html).toContain("Cargar catalogos");
    expect(html).toContain("/rider");
  });

  it("renders rider portal key content", () => {
    const html = renderToStaticMarkup(<RiderPortalPage />);

    expect(html).toContain("Portal Rider");
    expect(html).toContain("Seguimiento de Entrega");
    expect(html).toContain("Actualizar etapa");
    expect(html).toContain("/station");
  });

  it("renders station portal key content", () => {
    const html = renderToStaticMarkup(<StationPortalPage />);

    expect(html).toContain("Portal Estacion");
    expect(html).toContain("Comisiones Semanales");
    expect(html).toContain("Cargar comisiones");
    expect(html).toContain("Cerrar semana");
  });
});

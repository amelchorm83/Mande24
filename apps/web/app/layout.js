import "./globals.css";

export const dynamic = "force-dynamic";

export const metadata = {
  title: {
    default: "Mande24 Logistics",
    template: "Mande24 | %s",
  },
  description: "Entrega segura. Ruta inteligente. Plataforma de logística para el sureste.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className="site-body">
        <div className="site-main">{children}</div>
        <footer className="site-footer" aria-label="Pie de pagina Mande24">
          <div className="site-footer-inner">
            <div className="site-footer-grid">
              <section className="site-footer-brand" aria-label="Presentacion de marca">
                <p className="site-footer-kicker">Mande24 Logistics</p>
                <h3 className="site-footer-title">Entrega segura. Ruta inteligente.</h3>
                <p className="site-footer-copy">
                  Operacion de ultima milla para Tabasco, Campeche, Chiapas, Yucatan y Quintana Roo con trazabilidad por tramos,
                  control de evidencias y tableros en tiempo real.
                </p>
                <div className="site-footer-pills">
                  <span>Mensajeria</span>
                  <span>Paqueteria</span>
                  <span>Mandaditos</span>
                </div>
              </section>

              <section className="site-footer-col" aria-label="Navegacion comercial">
                <p className="site-footer-col-title">Navegacion Comercial</p>
                <a href="/servicios">Servicios</a>
                <a href="/industrias">Industrias</a>
                <a href="/casos-exito">Casos de exito</a>
                <a href="/cotizador">Cotizador rapido</a>
              </section>

              <section className="site-footer-col" aria-label="Operacion y soporte">
                <p className="site-footer-col-title">Operacion y Soporte</p>
                <a href="/cobertura">Cobertura por zona</a>
                <a href="/rastreo-guia">Rastreo de guia</a>
                <a href="/niveles-servicio">Niveles de servicio</a>
                <a href="/centro-ayuda">Centro de ayuda</a>
              </section>

              <section className="site-footer-contact" aria-label="Contacto directo">
                <p className="site-footer-col-title">Contacto Directo</p>
                <p><strong>Telefono/WhatsApp:</strong> +52 993 343 8003</p>
                <p><strong>Horario:</strong> Lunes a sabado, 7:00 AM a 7:00 PM</p>
                <p><strong>Cobertura principal:</strong> Villahermosa, Cardenas, Tuxtla Gutierrez, Campeche, Merida, Cancun y rutas regionales.</p>
              </section>
            </div>

            <section className="site-footer-bottom" aria-label="Datos legales y operativos">
              <ul className="site-footer-metrics">
                <li><strong>Confirmacion operativa:</strong> menor a 5 minutos</li>
                <li><strong>Ventana urbana:</strong> 60-90 minutos segun zona</li>
                <li><strong>Trazabilidad:</strong> seguimiento por tramo y evidencia</li>
                <li><strong>Atencion:</strong> soporte humano en horario extendido</li>
              </ul>
              <div className="site-footer-legal-links" role="navigation" aria-label="Enlaces legales">
                <a href="/nosotros">Nosotros</a>
                <a href="/noticias">Noticias</a>
                <a href="/casos-exito">Casos de exito</a>
                <a href="/auth">Portal Acceso</a>
              </div>
              <div className="site-footer-actions" aria-label="Accion de contacto rapido">
                <a
                  className="btn whatsapp-btn site-footer-wa"
                  href="https://wa.me/529933438003"
                  target="_blank"
                  rel="noreferrer"
                >
                  <span className="site-footer-wa-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" role="img" focusable="false">
                      <path d="M20.52 3.48A11.8 11.8 0 0 0 12.02 0 11.97 11.97 0 0 0 1.68 18.07L0 24l6.13-1.61A11.98 11.98 0 0 0 24 11.98c0-3.2-1.25-6.2-3.48-8.5Zm-8.5 18.5h-.01a9.94 9.94 0 0 1-5.05-1.38l-.36-.22-3.64.95.98-3.55-.24-.36A9.97 9.97 0 1 1 12.02 21.98Zm5.47-7.47c-.3-.15-1.75-.87-2.02-.96-.27-.1-.46-.15-.66.15-.2.3-.76.96-.93 1.15-.17.2-.34.22-.64.07-.3-.15-1.25-.46-2.38-1.47-.88-.78-1.47-1.75-1.64-2.04-.17-.3-.02-.45.13-.6.13-.13.3-.34.44-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.66-1.58-.9-2.17-.24-.56-.48-.48-.66-.49h-.56c-.2 0-.52.08-.8.37-.27.3-1.05 1.02-1.05 2.49s1.08 2.88 1.23 3.08c.15.2 2.12 3.23 5.14 4.53.72.31 1.28.5 1.72.64.72.23 1.38.2 1.9.12.58-.09 1.75-.72 2-1.42.24-.7.24-1.3.17-1.42-.08-.12-.27-.2-.57-.35Z" />
                    </svg>
                  </span>
                  <span>Iniciar conversacion por WhatsApp</span>
                </a>
              </div>
              <p className="site-footer-meta">
                {new Date().getFullYear()} Mande24. Plataforma logistica con enfoque operativo,
                comercial y trazabilidad por guia.
              </p>
              <p className="site-footer-revision">Revision 2026-03-10</p>
            </section>
          </div>
        </footer>
      </body>
    </html>
  );
}

import "./globals.css";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Mande24 Logistics",
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
                <a
                  className="btn whatsapp-btn site-footer-wa"
                  href="https://wa.me/529933438003"
                  target="_blank"
                  rel="noreferrer"
                >
                  Iniciar conversacion por WhatsApp
                </a>
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

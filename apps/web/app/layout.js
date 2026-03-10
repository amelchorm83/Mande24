import "./globals.css";

export const metadata = {
  title: "Mande24 Logistics",
  description: "Entrega segura. Ruta inteligente. Plataforma de logística para Tabasco.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className="site-body">
        <div className="site-main">{children}</div>
        <footer className="site-footer" aria-label="Pie de pagina Mande24">
          <div className="site-footer-inner">
            <div>
              <p className="site-footer-title">Mande24 | Propuesta Inteligente</p>
              <p className="site-footer-copy">Logística de última milla para Tabasco y Campeche con trazabilidad, control operativo y atención rápida.</p>
            </div>
            <div className="site-footer-contact">
              <p><strong>Teléfono/WhatsApp:</strong> +52 993 343 8003</p>
              <p><strong>Horario:</strong> Lunes a Sábado de 7:00AM a 7:00PM</p>
              <a
                className="btn whatsapp-btn site-footer-wa"
                href="https://wa.me/529933438003"
                target="_blank"
                rel="noreferrer"
              >
                Escribir por WhatsApp
              </a>
            </div>
            <div className="site-footer-links" role="navigation" aria-label="Enlaces del pie de página">
              <a href="/servicios">Servicios</a>
              <a href="/cobertura">Cobertura</a>
              <a href="/contacto">Contacto</a>
              <a href="/centro-ayuda">Centro de Ayuda</a>
            </div>
            <p className="site-footer-meta">{new Date().getFullYear()} Mande24. Entrega segura, ruta inteligente.</p>
            <p className="site-footer-revision">Revisión 2026-03-09</p>
          </div>
        </footer>
      </body>
    </html>
  );
}

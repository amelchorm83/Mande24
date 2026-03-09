import "./globals.css";

export const metadata = {
  title: "Mande24 Logistics",
  description: "Entrega segura. Ruta inteligente. Plataforma de logistica para Tabasco.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}

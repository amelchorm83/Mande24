import "./globals.css";

export const metadata = {
  title: "Mande24 Independent",
  description: "Portal base para cliente, rider y estacion",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}

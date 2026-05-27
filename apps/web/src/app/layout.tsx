import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Megapolis Elevator Traceability",
  description: "Technical traceability for elevator load tests and fine leveling.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}

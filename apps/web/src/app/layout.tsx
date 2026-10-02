import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Satark Saathi",
  description:
    "Privacy-first scam check application for Indian senior citizens",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CREED - Project Delivery Intelligence",
  description: "Reversible Self-Learning Project Delivery Intelligence & Assurance Platform",
  icons: {
    icon: "/icon.png",
    shortcut: "/icon.png",
    apple: "/apple-icon.png",
  },
  openGraph: {
    title: "CREED - Project Delivery Intelligence",
    description: "Reversible Self-Learning Project Delivery Intelligence & Assurance Platform",
    images: [{ url: "/creed-logo.png" }],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

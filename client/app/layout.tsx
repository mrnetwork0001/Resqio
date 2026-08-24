import type { Metadata } from "next";
import { Anton, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const display = Anton({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-display",
});
const body = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-body",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Resqio — Autonomous Community Crisis Logistics",
  description:
    "An AI agent that watches weather and grid feeds 24/7, matches neighbors' spare resources to urgent needs over SMS, and pings volunteers on WhatsApp only when a delivery needs human approval.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable} ${mono.variable} bg-ground text-ink font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}

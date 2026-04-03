import type { Metadata } from "next";
import { Inter, Lora } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/layout/nav";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "RevSight | Revenue Command Copilot",
  description:
    "AI-powered pipeline health analysis for CROs, RevOps leads, and data engineers. " +
    "Real-time insights, risk detection, and automated QBR reporting.",
  keywords: ["revenue operations", "pipeline health", "AI agents", "sales analytics", "CRM"],
};

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: 'swap' });
const lora = Lora({ subsets: ["latin"], variable: "--font-lora", display: 'swap' });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${lora.variable}`} suppressHydrationWarning>
      <body>
        <Nav />
        {/* Offset: 256px on desktop, 56px top bar on mobile */}
        <main
          className="md:pl-64 transition-all duration-200"
          style={{ minHeight: "100vh", position: "relative" }}
        >
          <div className="block md:hidden h-14" /> {/* mobile top-bar spacer */}
          {children}
        </main>
        <Toaster position="bottom-right" theme="dark" />
      </body>
    </html>
  );
}

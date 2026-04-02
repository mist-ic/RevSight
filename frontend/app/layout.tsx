import type { Metadata } from "next";
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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Nav />
        <main
          style={{
            marginLeft: "256px",
            minHeight: "100vh",
            position: "relative",
          }}
        >
          {children}
        </main>
        <Toaster position="bottom-right" theme="dark" />
      </body>
    </html>
  );
}

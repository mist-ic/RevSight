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
        <div className="flex min-h-screen">
          <Nav />
          <main className="flex-1 ml-64 min-h-screen">
            {children}
          </main>
        </div>
        <Toaster position="bottom-right" theme="dark" />
      </body>
    </html>
  );
}

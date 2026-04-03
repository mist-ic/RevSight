import type { Metadata } from "next";
import { Syne, Space_Mono } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/layout/nav";

const syne = Syne({ 
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-syne",
});

const spaceMono = Space_Mono({ 
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "RevSight | Command",
  description: "Enterprise Pipeline Analysis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${syne.variable} ${spaceMono.variable} dark`} suppressHydrationWarning>
      <body className="antialiased text-foreground bg-background selection:bg-primary selection:text-black">
        <div className="flex h-screen w-full overflow-hidden">
          {/* Static Sidebar ensuring zero overlap */}
          <div className="w-72 flex-shrink-0 border-r border-border hidden md:block relative z-20">
            <Nav />
          </div>
          
          {/* Main Content Pane */}
          <main className="flex-1 h-screen overflow-hidden bg-background relative z-10">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

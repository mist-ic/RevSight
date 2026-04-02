"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Activity,
  FileText,
  Home,
  Zap,
} from "lucide-react";

const links = [
  { href: "/",           label: "Home",    icon: Home },
  { href: "/reports",    label: "Reports", icon: FileText },
  { href: "/runs",       label: "Runs",    icon: Activity },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <aside
      className="fixed left-0 top-0 h-full w-64 flex flex-col z-40"
      style={{
        background: "linear-gradient(180deg, hsl(222 47% 7%) 0%, hsl(222 47% 5%) 100%)",
        borderRight: "1px solid var(--glass-border)",
      }}
    >
      {/* Logo */}
      <div className="px-6 py-6 border-b" style={{ borderColor: "var(--glass-border)" }}>
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center animate-pulse-glow"
            style={{ background: "var(--gradient-brand)" }}
          >
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-semibold text-sm leading-tight gradient-text">RevSight</p>
            <p className="text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
              Revenue Copilot
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
              style={{
                color: active ? "hsl(var(--primary))" : "hsl(var(--muted-foreground))",
                background: active ? "hsla(217, 91%, 60%, 0.1)" : "transparent",
                border: active ? "1px solid hsla(217, 91%, 60%, 0.2)" : "1px solid transparent",
              }}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div
        className="px-6 py-4 border-t"
        style={{ borderColor: "var(--glass-border)" }}
      >
        <p className="text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
          Phase 1 Build
        </p>
        <p className="text-xs font-medium mt-0.5" style={{ color: "hsl(var(--foreground))" }}>
          LangGraph + Pydantic AI
        </p>
      </div>
    </aside>
  );
}

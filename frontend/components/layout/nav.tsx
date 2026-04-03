"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Activity, FileText, Home, Zap, Menu, X } from "lucide-react";

const links = [
  { href: "/",        label: "Home",    icon: Home },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/runs",    label: "Runs",    icon: Activity },
];

function NavLinks({ pathname, onClick }: { pathname: string; onClick?: () => void }) {
  return (
    <nav className="flex-1 px-3 py-4 space-y-1">
      {links.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || (href !== "/" && pathname.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            onClick={onClick}
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
  );
}

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const logo = (
    <div className="flex items-center gap-3">
      <div
        className="w-9 h-9 rounded-xl flex items-center justify-center animate-pulse-glow shrink-0"
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
  );

  const footer = (
    <div className="px-6 py-4 border-t" style={{ borderColor: "var(--glass-border)" }}>
      <p className="text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
        LangGraph + Pydantic AI
      </p>
      <p className="text-xs font-medium mt-0.5" style={{ color: "hsl(var(--foreground))" }}>
        Gemini 3 Flash Preview
      </p>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className="fixed left-0 top-0 h-full w-64 flex-col z-40 hidden md:flex"
        style={{
          background: "linear-gradient(180deg, hsl(222 47% 7%) 0%, hsl(222 47% 5%) 100%)",
          borderRight: "1px solid var(--glass-border)",
        }}
      >
        <div className="px-6 py-6 border-b" style={{ borderColor: "var(--glass-border)" }}>
          {logo}
        </div>
        <NavLinks pathname={pathname} />
        {footer}
      </aside>

      {/* Mobile top bar */}
      <div
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 py-3 md:hidden"
        style={{
          background: "hsl(222 47% 7%)",
          borderBottom: "1px solid var(--glass-border)",
        }}
      >
        {logo}
        <button
          onClick={() => setOpen(!open)}
          className="p-2 rounded-lg"
          style={{ color: "hsl(var(--muted-foreground))" }}
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          onClick={() => setOpen(false)}
        >
          <div className="absolute inset-0" style={{ background: "hsla(0,0%,0%,0.5)" }} />
          <aside
            className="absolute left-0 top-0 h-full w-64 flex flex-col"
            style={{
              background: "linear-gradient(180deg, hsl(222 47% 7%) 0%, hsl(222 47% 5%) 100%)",
              borderRight: "1px solid var(--glass-border)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-6 border-b" style={{ borderColor: "var(--glass-border)" }}>
              {logo}
            </div>
            <NavLinks pathname={pathname} onClick={() => setOpen(false)} />
            {footer}
          </aside>
        </div>
      )}
    </>
  );
}

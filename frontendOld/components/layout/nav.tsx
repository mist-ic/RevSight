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
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
              active 
                ? "text-primary bg-primary/10 border border-primary/20" 
                : "text-muted-foreground border border-transparent hover:bg-muted"
            }`}
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
      <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-primary shrink-0 transition-transform hover:scale-105">
        <Zap className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="font-semibold text-sm leading-tight text-foreground font-serif">RevSight</p>
        <p className="text-xs text-muted-foreground">Revenue Copilot</p>
      </div>
    </div>
  );

  const footer = (
    <div className="px-6 py-4 border-t border-border">
      <p className="text-xs text-muted-foreground">LangGraph + Pydantic AI</p>
      <p className="text-xs font-medium mt-0.5 text-foreground">Gemini 3 Flash Preview</p>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 flex-col z-40 hidden md:flex bg-card border-r border-border shadow-sm">
        <div className="px-6 py-6 border-b border-border">
          {logo}
        </div>
        <NavLinks pathname={pathname} />
        {footer}
      </aside>

      {/* Mobile top bar */}
      <div className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 py-3 md:hidden bg-card border-b border-border shadow-sm">
        {logo}
        <button
          onClick={() => setOpen(!open)}
          className="p-2 rounded-lg text-muted-foreground hover:bg-muted"
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
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
          <aside
            className="absolute left-0 top-0 h-full w-64 flex flex-col bg-card border-r border-border"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-6 border-b border-border">
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

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "01 // OVERVIEW" },
  { href: "/reports", label: "02 // INTELLIGENCE" },
  { href: "/runs", label: "03 // RUN TRACES" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col h-full bg-[#050505]">
      {/* Brutalist Logo Block */}
      <div className="p-8 border-b border-border">
        <h1 className="text-5xl font-extrabold text-white tracking-tighter leading-none mb-3">
          RS_
        </h1>
        <div className="font-data text-[10px] text-primary uppercase tracking-[0.25em] font-bold">
          Revenue Command // V2
        </div>
      </div>

      <nav className="flex-1 p-6 space-y-2 mt-4">
        {links.map(({ href, label }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`block w-full py-4 text-xs font-data transition-all border-b ${
                active 
                  ? "text-primary border-primary font-bold" 
                  : "text-muted-foreground border-transparent hover:text-white"
              }`}
            >
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Connection StatusBar */}
      <div className="p-6 border-t border-border bg-[#0a0a0a]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-primary drop-shadow-[0_0_8px_rgba(229,255,0,0.8)] animate-pulse rounded-full" />
            <span className="font-data text-[9px] uppercase font-bold tracking-[0.2em] text-primary">Live Sync</span>
          </div>
          <span className="font-data text-[9px] text-muted-foreground">NODE_01</span>
        </div>
      </div>
    </div>
  );
}

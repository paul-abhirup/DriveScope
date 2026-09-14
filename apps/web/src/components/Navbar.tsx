"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Film, 
  FlaskConical, 
  PlayCircle, 
  SlidersHorizontal, 
  AlertTriangle, 
  Cpu 
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/scenarios", label: "Scenarios", icon: Film },
    { href: "/experiments/new", label: "Experiment Builder", icon: FlaskConical },
    { href: "/runs", label: "Runs & Monitor", icon: PlayCircle },
    { href: "/compare", label: "Compare & Robustness", icon: SlidersHorizontal },
    { href: "/failures", label: "Failure Explorer", icon: AlertTriangle },
    { href: "/models", label: "VLA Adapters", icon: Cpu },
  ];

  return (
    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg tracking-tight text-zinc-100 hover:text-emerald-400 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-mono text-sm">
              DS
            </div>
            <span>DriveScope</span>
          </Link>
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-zinc-800 text-emerald-400 border border-zinc-700/60"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/40 text-emerald-400 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Mode: Minimal / CPU
          </div>
        </div>
      </div>
    </header>
  );
}

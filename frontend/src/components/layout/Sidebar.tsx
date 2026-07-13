"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { 
  Home, 
  Sparkles, 
  Scale, 
  Library, 
  Heart, 
  Star, 
  History, 
  Quote
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  className?: string;
}

function SidebarContent({ className }: SidebarProps) {
  const searchParams = useSearchParams();
  const activeTab = searchParams.get("tab") || "Home";

  const menuItems = [
    { name: "Home", icon: Home, label: "Home" },
    { name: "Recommendations", icon: Sparkles, label: "Discover" },
    { name: "Compare", icon: Scale, label: "Compare Books" },
    { name: "Shelf", icon: Library, label: "My Shelf" },
    { name: "Mood", icon: Heart, label: "Mood Journal" },
    { name: "Favorites", icon: Star, label: "Favorites" },
    { name: "History", icon: History, label: "History" },
  ];

  const tasteProfile = [
    { label: "Genres", values: ["Fantasy", "Romance"] },
    { label: "Pacing", values: ["Slow Burn"] },
    { label: "Vibe", values: ["Mild Romance"] },
    { label: "Cohort", values: ["18–24"] },
  ];

  return (
    <aside className={cn("w-72 flex flex-col gap-6 p-6 border-r glass-panel h-screen sticky top-0 shrink-0 select-none z-30", className)}>
      {/* Logo */}
      <div className="flex flex-col gap-1.5 px-2">
        <Link href="/?tab=Home" className="group flex items-center gap-2.5">
          <span className="text-3xl font-heading font-bold text-gradient-gold tracking-tight group-hover:scale-[1.02] transition-transform duration-300">
            BookSoul
          </span>
          <span className="text-xl animate-pulse">🔮</span>
        </Link>
        <span className="text-xs text-muted-foreground/80 tracking-wide font-sans">
          Books that understand you.
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1">
        <div className="text-[10px] font-bold text-muted-foreground/50 tracking-widest px-2 mb-2 uppercase">
          Navigation
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.name;

          return (
            <Link
              key={item.name}
              href={`/?tab=${item.name}`}
              className={cn(
                "flex items-center gap-3.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 relative group",
                isActive
                  ? "bg-accent-purple/10 text-accent-purple border-l-2 border-accent-purple shadow-[0_0_15px_rgba(167,139,250,0.1)]"
                  : "text-muted-foreground hover:bg-white/[0.03] hover:text-foreground"
              )}
            >
              <Icon className={cn(
                "w-4 h-4 transition-transform duration-300 group-hover:scale-110",
                isActive ? "text-accent-purple" : "text-muted-foreground/75 group-hover:text-foreground"
              )} />
              <span>{item.label}</span>
              {isActive && (
                <span className="absolute right-3 w-1.5 h-1.5 rounded-full bg-accent-purple" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Taste Profile Panel */}
      <div className="border-t border-white/[0.05] pt-5 flex flex-col gap-3">
        <div className="flex items-center justify-between px-2">
          <span className="text-[10px] font-bold text-muted-foreground/50 tracking-widest uppercase">
            Taste DNA
          </span>
          <span className="text-[10px] font-semibold text-accent-purple hover:underline cursor-pointer">
            Edit
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5 px-1 max-h-36 overflow-y-auto pr-1">
          {tasteProfile.flatMap((category) => 
            category.values.map((val) => (
              <span 
                key={val} 
                className="text-[11px] font-medium bg-white/[0.02] border border-white/[0.05] px-2.5 py-1 rounded-full text-muted-foreground/90 hover:border-accent-purple/30 hover:text-foreground transition-all duration-300 cursor-default"
              >
                {val}
              </span>
            ))
          )}
        </div>
      </div>

      {/* Daily Wisdom / Quote Card */}
      <div className="mt-auto border-t border-white/[0.05] pt-5">
        <div className="glass-panel p-4 rounded-2xl flex flex-col gap-2 bg-white/[0.01] hover:bg-white/[0.02] transition-colors duration-500 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-3 opacity-5 group-hover:opacity-10 transition-opacity duration-500">
            <Quote className="w-12 h-12 text-accent-gold" />
          </div>
          <span className="text-[9px] font-bold tracking-wider text-accent-gold uppercase flex items-center gap-1">
            <Quote className="w-2.5 h-2.5" /> Reader Wisdom
          </span>
          <p className="text-[11px] leading-relaxed text-muted-foreground/95 italic">
            &ldquo;Books are a uniquely portable magic.&rdquo;
          </p>
          <span className="text-[10px] font-semibold text-muted-foreground/50 self-end mt-1">
            — Stephen King
          </span>
        </div>
      </div>
    </aside>
  );
}

export default function Sidebar({ className }: SidebarProps) {
  return (
    <Suspense fallback={
      <aside className={cn("w-72 flex flex-col gap-6 p-6 border-r glass-panel h-screen sticky top-0 shrink-0 select-none z-30 animate-pulse", className)}>
        <div className="h-8 w-32 bg-white/[0.05] rounded-lg" />
        <div className="h-6 w-20 bg-white/[0.02] rounded-lg mt-4" />
        <div className="flex flex-col gap-2 mt-2">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="h-10 w-full bg-white/[0.02] rounded-xl" />
          ))}
        </div>
      </aside>
    }>
      <SidebarContent className={className} />
    </Suspense>
  );
}

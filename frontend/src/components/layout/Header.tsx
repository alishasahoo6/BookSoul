"use client";

import { useEffect, useState, Suspense } from "react";
import { usePathname } from "next/navigation";
import { Search } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

function HeaderContent() {
  const pathname = usePathname();
  const [greeting, setGreeting] = useState("Good evening");

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) setGreeting("Good morning");
    else if (hour < 17) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  const getBreadcrumb = () => {
    if (pathname === "/") return "Home";
    const segment = pathname.substring(1);
    return segment.charAt(0).toUpperCase() + segment.slice(1);
  };

  return (
    <header className="h-16 border-b border-white/[0.05] bg-background/30 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20 select-none">
      {/* Left: Breadcrumbs & Greeting */}
      <div className="flex items-center gap-4">
        <div className="flex flex-col">
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground/60 font-medium font-sans">
            BookSoul / {getBreadcrumb()}
          </div>
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5 mt-0.5 font-sans">
            <span>{greeting}, Reader</span>
            <span className="animate-wiggle">👋</span>
          </h2>
        </div>
      </div>

      {/* Middle: Visual CMD+K Search bar (placeholder) */}
      <div className="hidden md:flex items-center gap-2 bg-white/[0.02] hover:bg-white/[0.04] border border-white/[0.05] rounded-full px-4 py-1.5 w-96 transition-all duration-300 cursor-not-allowed group">
        <Search className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground/80 transition-colors" />
        <span className="text-xs text-muted-foreground/60 flex-1 truncate">
          Find by title, theme, trope, or vibe...
        </span>
        <kbd className="text-[10px] font-mono bg-white/[0.05] text-muted-foreground/70 px-1.5 py-0.5 rounded border border-white/[0.05]">
          ⌘K
        </kbd>
      </div>

      {/* Right: Core Engine Status & Profile */}
      <div className="flex items-center gap-5">
        {/* Core engine status badge */}
        <div className="hidden sm:flex items-center gap-2 bg-accent-gold/5 border border-accent-gold/10 px-3 py-1 rounded-full text-[10px] text-accent-gold font-medium">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-gold opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-gold"></span>
          </span>
          <span>DNA Engine Active</span>
        </div>

        {/* User avatar */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex flex-col text-right">
            <span className="text-xs font-semibold text-foreground">Alisha Sahoo</span>
            <span className="text-[9px] text-muted-foreground/75 font-medium">Premium Reader</span>
          </div>
          <Avatar className="h-8 w-8 ring-1 ring-white/10 hover:ring-accent-purple/50 cursor-pointer transition-all duration-300">
            <AvatarImage src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=256&auto=format&fit=crop" alt="User avatar" />
            <AvatarFallback className="bg-accent-purple/20 text-accent-purple text-xs font-bold">AS</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  );
}

export default function Header() {
  return (
    <Suspense fallback={
      <header className="h-16 border-b border-white/[0.05] bg-background/30 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20 animate-pulse">
        <div className="h-6 w-32 bg-white/[0.03] rounded" />
        <div className="h-8 w-96 bg-white/[0.02] rounded-full hidden md:block" />
        <div className="h-8 w-8 rounded-full bg-white/[0.03]" />
      </header>
    }>
      <HeaderContent />
    </Suspense>
  );
}

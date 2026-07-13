"use client";

import Link from "next/link";
import { BookOpen } from "lucide-react";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-white/[0.05] bg-black/20 py-8 px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground select-none">
      <div className="flex items-center gap-2">
        <BookOpen className="w-3.5 h-3.5 text-accent-gold" />
        <span>&copy; {currentYear} BookSoul. Discover books that touch your soul.</span>
      </div>

      <div className="flex items-center gap-6">
        <Link href="#" className="hover:text-foreground transition-colors duration-300">
          About
        </Link>
        <Link href="#" className="hover:text-foreground transition-colors duration-300">
          Privacy Policy
        </Link>
        <Link href="#" className="hover:text-foreground transition-colors duration-300">
          Terms of Service
        </Link>
        <Link href="#" className="hover:text-foreground transition-colors duration-300">
          Support
        </Link>
      </div>
    </footer>
  );
}

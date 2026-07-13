"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  ArrowRight,
  TrendingUp,
  BarChart3,
  BookOpen,
  Library,
  ChevronRight,
  AlertTriangle,
  RefreshCw
} from "lucide-react";
import { Button } from "@/components/ui/button";

// Cycling loader texts
const LOADING_STEPS = [
  "Contacting BookSoul DNA Engine...",
  "Analyzing emotional vibes and context...",
  "Inhaling candidate literary tropes...",
  "Evaluating writing styles and pacing...",
  "Calculating semantic alignment score...",
  "Constructing your personalized catalog..."
];

function HomeDashboard() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaderStep, setLoaderStep] = useState(0);

  // Cycle loading messages
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      setLoaderStep(0);
      interval = setInterval(() => {
        setLoaderStep((prev) => (prev + 1) % LOADING_STEPS.length);
      }, 1800);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSearch = async (queryText?: string) => {
    const activeQuery = queryText !== undefined ? queryText : searchQuery;
    if (!activeQuery.trim()) {
      alert("Please describe a vibe or mood first!");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: activeQuery, n_results: 8 }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || `HTTP Error ${res.status}`);
      }

      const data = await res.json();
      
      // Store result and query in sessionStorage
      sessionStorage.setItem("booksoul_recommendations", JSON.stringify(data.results || []));
      sessionStorage.setItem("booksoul_query", activeQuery);

      // Save search to timeline history in localStorage
      const historyStr = localStorage.getItem("booksoul_history");
      let historyArr: string[] = [];
      if (historyStr) {
        try {
          historyArr = JSON.parse(historyStr);
        } catch (e) {
          console.error(e);
        }
      }
      const matchText = `Searched: "${activeQuery}" (Returned ${data.results?.length || 0} matches)`;
      if (!historyArr.includes(matchText)) {
        historyArr.unshift(matchText);
        localStorage.setItem("booksoul_history", JSON.stringify(historyArr.slice(0, 10)));
      }

      // Navigate to discover view
      router.push("/discover");

    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to contact the BookSoul engine.");
    } finally {
      setLoading(false);
    }
  };

  const popularMoods = [
    { label: "Pulse-Pounding & Wild", emoji: "⚡", query: "pulse-pounding wild thriller action" },
    { label: "Atmospheric & Dread-Soaked", emoji: "🕯️", query: "atmospheric dread gothic horror" },
    { label: "Cozy Romance", emoji: "☕", query: "cozy sweet romance small town" },
    { label: "Mind-Bending & Tense", emoji: "🌀", query: "mind-bending tense psychological thriller" },
    { label: "Intimate & Raw", emoji: "🍷", query: "intimate raw emotional drama" },
    { label: "Fast-Paced & Gripping", emoji: "🚀", query: "fast-paced gripping sci-fi adventure" },
    { label: "Magical & Immersive", emoji: "🔮", query: "magical immersive high fantasy" },
    { label: "Deeply Introspective", emoji: "🌲", query: "deeply introspective slow burn contemporary" },
  ];

  return (
    <div className="flex flex-col gap-10 w-full relative font-sans">
      
      {/* Premium Loader Overlay */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-md z-50 flex flex-col items-center justify-center gap-4"
          >
            {/* Pulsing Portal Orb */}
            <div className="relative flex h-16 w-16 items-center justify-center">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-purple opacity-40"></span>
              <div className="relative rounded-full h-10 w-10 bg-gradient-purple-pink flex items-center justify-center shadow-[0_0_25px_rgba(167,139,250,0.5)]">
                <span className="text-xl animate-spin">🔮</span>
              </div>
            </div>
            
            <div className="flex flex-col items-center gap-1.5 text-center px-4 max-w-sm mt-2">
              <motion.span
                key={loaderStep}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="text-sm font-semibold text-accent-gold"
              >
                {LOADING_STEPS[loaderStep]}
              </motion.span>
              <span className="text-[10px] text-muted-foreground/65">Calculating neural narrative vectors...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Overlay */}
      {error && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md z-50 flex items-center justify-center p-6">
          <div className="glass-panel p-8 rounded-2xl border-destructive/20 bg-destructive/5 flex flex-col items-center text-center gap-4 max-w-xl">
            <div className="p-3 bg-destructive/10 rounded-full text-destructive border border-destructive/20">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="flex flex-col gap-1">
              <h4 className="text-sm font-semibold text-foreground">Recommendation Engine Offline</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {error}
              </p>
            </div>
            <div className="flex gap-3 mt-2">
              <Button
                onClick={() => handleSearch()}
                className="bg-white/[0.05] border border-white/10 hover:bg-white/[0.1] text-foreground rounded-full text-xs px-5 py-2.5 font-medium flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Retry Request
              </Button>
              <Button
                onClick={() => setError(null)}
                className="bg-gradient-purple-pink text-white rounded-full text-xs px-5 py-2.5 font-medium"
              >
                Dismiss
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="relative rounded-3xl overflow-hidden glass-panel p-8 md:p-12 shadow-[0_20px_50px_rgba(0,0,0,0.3)] border-gradient-glow">
        {/* Soft background gradient glows */}
        <div className="absolute top-0 left-0 -translate-x-1/4 -translate-y-1/4 w-96 h-96 bg-accent-purple/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-0 right-0 translate-x-1/4 translate-y-1/4 w-96 h-96 bg-accent-pink/10 rounded-full blur-[100px] pointer-events-none" />
        
        <div className="max-w-2xl relative z-10 flex flex-col items-start gap-4">
          <div className="inline-flex items-center gap-1.5 bg-accent-gold/10 border border-accent-gold/20 px-3 py-1 rounded-full text-xs font-semibold text-accent-gold tracking-wide">
            <Sparkles className="w-3 h-3 animate-pulse" /> Introducing BookSoul DNA
          </div>
          <h1 className="text-4xl md:text-5xl font-heading font-bold text-gradient-gold leading-tight tracking-tight mt-2">
            Discover books that <br />
            truly understand you.
          </h1>
          <p className="text-sm md:text-base text-muted-foreground/90 leading-relaxed font-sans font-light mt-2 max-w-xl">
            BookSoul shifts literary discovery from simple queries to deep semantic matching. 
            Describe your mood, select your favorite genres, and explore literature tailored to 
            your exact emotional DNA, pacing style, and character tropes.
          </p>

          {/* Connected Search Input Panel */}
          <div className="flex flex-col sm:flex-row gap-3 w-full max-w-xl mt-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Describe your current vibe (e.g. small town romance, enemies to lovers)..."
                className="w-full bg-white/[0.03] border border-white/10 rounded-full py-3.5 pl-5 pr-4 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:border-accent-purple/50 focus:ring-1 focus:ring-accent-purple/20 transition-all duration-300"
              />
            </div>
            <Button 
              onClick={() => handleSearch()}
              className="bg-gradient-purple-pink hover:opacity-90 rounded-full px-6 py-3.5 text-xs font-semibold transition-all duration-300 flex items-center gap-2 cursor-pointer shadow-[0_4px_20px_rgba(167,139,250,0.25)] shrink-0"
            >
              <span>Begin Exploration</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* Popular Moods */}
      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <h3 className="text-lg font-heading font-semibold text-foreground">What&apos;s your current vibe?</h3>
            <p className="text-xs text-muted-foreground">Select a literary mood or pacing to populate recommendations</p>
          </div>
          <span 
            onClick={() => router.push("/discover")}
            className="text-xs text-accent-purple hover:underline cursor-pointer font-medium flex items-center gap-1"
          >
            See all moods <ChevronRight className="w-3 h-3" />
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mt-1">
          {popularMoods.map((mood, idx) => (
            <motion.div
              whileHover={{ y: -3, borderColor: "rgba(167, 139, 250, 0.3)" }}
              onClick={() => handleSearch(mood.query)}
              key={idx}
              className="glass-panel p-4 rounded-xl flex flex-col items-center justify-center gap-3 text-center cursor-pointer select-none transition-all duration-300 hover:bg-white/[0.02]"
            >
              <span className="text-2xl">{mood.emoji}</span>
              <span className="text-[11px] font-medium text-muted-foreground/90 leading-tight">
                {mood.label}
              </span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Insights & Metrics Dashboard */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reading Analytics */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-5 bg-white/[0.01]">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-accent-purple/10 border border-accent-purple/20">
              <BarChart3 className="w-4 h-4 text-accent-purple" />
            </div>
            <div className="flex flex-col">
              <h4 className="text-sm font-semibold text-foreground">Reading DNA Analytics</h4>
              <span className="text-[10px] text-muted-foreground">Dynamic affinity distribution</span>
            </div>
          </div>

          <div className="flex flex-col gap-3.5 mt-2">
            {[
              { genre: "Fantasy & Magic", pct: 60, color: "var(--accent-purple)" },
              { genre: "Contemporary Romance", pct: 30, color: "var(--accent-pink)" },
              { genre: "Sci-Fi & Speculative", pct: 10, color: "var(--accent-gold)" },
            ].map((item) => (
              <div key={item.genre} className="flex flex-col gap-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-muted-foreground">{item.genre}</span>
                  <span className="text-foreground/90">{item.pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${item.pct}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    style={{ backgroundColor: item.color }} 
                    className="h-full rounded-full" 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sentiment Journal Status */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col gap-5 bg-white/[0.01]">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-accent-gold/10 border border-accent-gold/20">
              <TrendingUp className="w-4 h-4 text-accent-gold" />
            </div>
            <div className="flex flex-col">
              <h4 className="text-sm font-semibold text-foreground">Sentiment Summary</h4>
              <span className="text-[10px] text-muted-foreground">Based on your recent logs</span>
            </div>
          </div>

          <div className="flex-1 flex flex-col justify-center gap-3">
            <div className="text-xs text-muted-foreground leading-relaxed">
              Your profile is currently tuned to <span className="text-accent-purple font-medium">Reflective & Cozy</span>. 
              The system is prioritizing slow-burn pacing, emotional depth, and heavy character growth in recommendations.
            </div>
            <div className="flex gap-2 mt-2">
              <span className="text-[10px] bg-accent-purple/10 border border-accent-purple/20 text-accent-purple px-2.5 py-0.5 rounded-full font-medium">Slow Burn (8/10)</span>
              <span className="text-[10px] bg-accent-pink/10 border border-accent-pink/20 text-accent-pink px-2.5 py-0.5 rounded-full font-medium">High Angst (4/10)</span>
              <span className="text-[10px] bg-accent-gold/10 border border-accent-gold/20 text-accent-gold px-2.5 py-0.5 rounded-full font-medium">Cozy Atmosphere</span>
            </div>
          </div>
        </div>
      </section>

      {/* Feed Placeholder Area */}
      <section className="border-t border-white/[0.05] pt-8 flex flex-col gap-4">
        <div className="flex flex-col gap-0.5">
          <h3 className="text-lg font-heading font-semibold text-foreground">Your Discovery Feed</h3>
          <p className="text-xs text-muted-foreground">Personalized matches appear here</p>
        </div>

        {/* Elegant Placeholder Screen */}
        <div 
          onClick={() => router.push("/discover")}
          className="border border-dashed border-white/10 rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 bg-white/[0.005] hover:bg-white/[0.01] transition-colors cursor-pointer"
        >
          <div className="w-12 h-12 rounded-full bg-white/[0.02] flex items-center justify-center border border-white/[0.05] mb-2">
            <BookOpen className="w-5 h-5 text-muted-foreground/60" />
          </div>
          <h4 className="text-sm font-semibold text-foreground">Explore Full Catalog</h4>
          <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
            Click here or submit a search description in the Hero Exploration bar above to query the semantic recommendation server.
          </p>
        </div>
      </section>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex flex-col items-center justify-center p-12 min-h-[50vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="text-3xl animate-bounce">🔮</div>
          <span className="text-sm text-muted-foreground animate-pulse font-medium">Opening BookSoul...</span>
        </div>
      </div>
    }>
      <HomeDashboard />
    </Suspense>
  );
}
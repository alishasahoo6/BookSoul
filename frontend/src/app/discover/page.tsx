"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Sparkles, 
  Compass, 
  Heart, 
  Star, 
  AlertTriangle,
  RefreshCw,
  Home,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface BookDNAModel {
  emotional_depth: number;
  comfort: number;
  humor: number;
  angst: number;
  spice: number;
  character_growth: number;
  pacing: number;
  atmosphere: string;
}

interface BookSoulModel {
  themes: string[];
  tropes: string[];
  emotional_tone: string;
  writing_style: string;
  pacing: string;
  character_dynamics: string;
  reader_vibe: string;
  emotional_arc: string;
  dna: BookDNAModel;
  is_fallback: boolean;
  is_antigravity: boolean;
}

interface BookRecommendation {
  id?: string;
  title: string;
  authors?: string;
  description?: string;
  cover_image?: string;
  subject?: string;
  quality_score: number;
  soul: BookSoulModel;
  distance_score: number;
  soul_match: number;
  hybrid_score: number;
  relevance_confidence: number;
  relevance_reason: string;
  match_reasons: string[];
}

// Cycling loader texts
const LOADING_STEPS = [
  "Contacting BookSoul DNA Engine...",
  "Analyzing emotional vibes and context...",
  "Inhaling candidate literary tropes...",
  "Evaluating writing styles and pacing...",
  "Calculating semantic alignment score...",
  "Constructing your personalized catalog..."
];

function DiscoverContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryParam = searchParams.get("query") || "";

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<BookRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [expandedMatch, setExpandedMatch] = useState<Record<string, boolean>>({});
  const [expandedDNA, setExpandedDNA] = useState<Record<string, boolean>>({});
  
  // Loader step index
  const [loaderStep, setLoaderStep] = useState(0);

  // Load favorites from local storage
  useEffect(() => {
    const favs = localStorage.getItem("booksoul_favorites");
    if (favs) {
      try {
        setFavorites(JSON.parse(favs));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  // Handle direct tab load / query param trigger
  useEffect(() => {
    if (queryParam) {
      setQuery(queryParam);
      fetchRecommendations(queryParam);
    } else {
      // Check session storage
      const cached = sessionStorage.getItem("booksoul_recommendations");
      const cachedQuery = sessionStorage.getItem("booksoul_query");
      if (cached) {
        try {
          setResults(JSON.parse(cached));
          if (cachedQuery) setQuery(cachedQuery);
        } catch (e) {
          console.error(e);
        }
      }
    }
  }, [queryParam]);

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

  const fetchRecommendations = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: searchQuery, n_results: 8 }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || `HTTP Error ${res.status}`);
      }

      const data = await res.json();
      setResults(data.results || []);
      
      // Store in session storage
      sessionStorage.setItem("booksoul_recommendations", JSON.stringify(data.results));
      sessionStorage.setItem("booksoul_query", searchQuery);

      // Save query to timeline history
      const historyStr = localStorage.getItem("booksoul_history");
      let historyArr: string[] = [];
      if (historyStr) {
        try {
          historyArr = JSON.parse(historyStr);
        } catch (e) {
          console.error(e);
        }
      }
      const matchText = `Searched: "${searchQuery}" (Returned ${data.results?.length || 0} matches)`;
      if (!historyArr.includes(matchText)) {
        historyArr.unshift(matchText);
        localStorage.setItem("booksoul_history", JSON.stringify(historyArr.slice(0, 10)));
      }

    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to fetch book matches from the backend.");
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (title: string) => {
    let updated = [...favorites];
    if (updated.includes(title)) {
      updated = updated.filter((t) => t !== title);
    } else {
      updated.push(title);
    }
    setFavorites(updated);
    localStorage.setItem("booksoul_favorites", JSON.stringify(updated));

    // Save action to timeline history
    const historyStr = localStorage.getItem("booksoul_history");
    let historyArr: string[] = [];
    if (historyStr) {
      try {
        historyArr = JSON.parse(historyStr);
      } catch (e) {}
    }
    const actionText = updated.includes(title) 
      ? `Favorited book: "${title}"`
      : `Removed favorite: "${title}"`;
    historyArr.unshift(actionText);
    localStorage.setItem("booksoul_history", JSON.stringify(historyArr.slice(0, 10)));
  };

  const toggleMatchExplanation = (id: string) => {
    setExpandedMatch((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleDNAView = (id: string) => {
    setExpandedDNA((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleQuerySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    router.push(`/discover?query=${encodeURIComponent(query)}`);
  };

  // Convert raw decimal soul matches to rounded percentages
  const formatMatchPercent = (score: number) => {
    if (score <= 0) return 0;
    if (score <= 1) return Math.round(score * 100);
    return Math.round(score);
  };

  return (
    <div className="flex flex-col gap-8 w-full relative min-h-[60vh] font-sans">
      
      {/* Search Header Form */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-heading font-bold text-gradient-gold">Curated Discoveries</h1>
          <p className="text-xs text-muted-foreground">Deep DNA matches generated by the semantic discovery pipeline</p>
        </div>
        
        {/* Inline Search Input */}
        <form onSubmit={handleQuerySubmit} className="flex gap-2 w-full md:w-auto max-w-md shrink-0">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search mood, trope, or vibe..."
            className="flex-1 md:w-64 bg-white/[0.03] border border-white/10 rounded-full px-4 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:border-accent-purple/50 focus:ring-1 focus:ring-accent-purple/20 transition-all"
          />
          <Button 
            type="submit"
            className="bg-gradient-purple-pink text-white rounded-full px-4 py-2 text-xs font-semibold hover:opacity-90 transition-opacity"
          >
            Refine
          </Button>
        </form>
      </div>

      {/* Premium Loader Overlay */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-background/80 backdrop-blur-md z-40 flex flex-col items-center justify-center min-h-[40vh] gap-4"
          >
            {/* Spinning Gold Portal Orb */}
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

      {/* API Failure State */}
      {error && (
        <div className="glass-panel p-8 rounded-2xl border-destructive/20 bg-destructive/5 flex flex-col items-center text-center gap-4 max-w-xl mx-auto my-6">
          <div className="p-3 bg-destructive/10 rounded-full text-destructive border border-destructive/20">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-semibold text-foreground">Recommendation Engine Error</h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {error}
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={() => fetchRecommendations(query)}
              className="bg-white/[0.05] border border-white/10 hover:bg-white/[0.1] text-foreground rounded-full text-xs px-4 py-2 font-medium flex items-center gap-1.5"
            >
              <RefreshCw className="w-3 h-3" /> Retry Connection
            </Button>
            <Button
              onClick={() => router.push("/")}
              className="bg-gradient-purple-pink text-white rounded-full text-xs px-4 py-2 font-medium flex items-center gap-1.5"
            >
              <Home className="w-3 h-3" /> Back to Dashboard
            </Button>
          </div>
        </div>
      )}

      {/* Empty Results / Search Prompt */}
      {!loading && !error && results.length === 0 && (
        <div className="border border-dashed border-white/10 rounded-2xl p-16 text-center flex flex-col items-center justify-center gap-4 bg-white/[0.005]">
          <div className="w-12 h-12 rounded-full bg-white/[0.02] flex items-center justify-center border border-white/[0.05] mb-2">
            <Compass className="w-5 h-5 text-muted-foreground/60" />
          </div>
          <h4 className="text-sm font-semibold text-foreground">No Books Found</h4>
          <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
            {query.trim() 
              ? "We couldn't resolve matches for this query. Try detailing a different pacing, genre, or mood description."
              : "Enter a search query in the headbar above or describe a mood on the dashboard to trigger curation."}
          </p>
          {!query.trim() && (
            <Button
              onClick={() => router.push("/")}
              className="bg-gradient-purple-pink text-white rounded-full text-xs px-5 py-2.5 font-semibold mt-2"
            >
              Explore Home
            </Button>
          )}
        </div>
      )}

      {/* Successful Results Grid */}
      {!loading && !error && results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {results.map((book) => {
            const bookId = book.id || book.title.toLowerCase().replace(/[^a-z0-9]/g, "");
            const isFav = favorites.includes(book.title);
            const isMatchExpanded = !!expandedMatch[bookId];
            const isDNAExpanded = !!expandedDNA[bookId];

            return (
              <div 
                key={bookId} 
                className="glass-panel p-4 rounded-2xl flex flex-col gap-3 relative select-none bg-white/[0.01] hover:border-white/10 hover:shadow-2xl transition-all duration-300 h-full"
              >
                {/* Match percentage badge */}
                <div className="absolute top-6 right-6 z-10 bg-accent-purple/90 backdrop-blur-md text-[10px] font-bold text-white px-2 py-0.5 rounded-md shadow-lg border border-white/10">
                  {formatMatchPercent(book.soul_match)}% Match
                </div>

                {/* Cover Image */}
                <div className="aspect-[2/3] w-full rounded-xl bg-white/[0.02] border border-white/[0.05] relative overflow-hidden flex items-center justify-center select-none group shrink-0">
                  {book.cover_image ? (
                    <img 
                      src={book.cover_image} 
                      alt={book.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-center p-4">
                      <Compass className="w-8 h-8 text-white/[0.05]" />
                      <span className="text-[10px] text-muted-foreground font-semibold line-clamp-2">{book.title}</span>
                    </div>
                  )}
                </div>

                {/* Action Buttons: Favorites */}
                <div className="flex justify-between items-start gap-2 mt-1">
                  <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                    <h3 className="text-sm font-heading font-bold text-foreground line-clamp-1 leading-tight" title={book.title}>
                      {book.title}
                    </h3>
                    <span className="text-[11px] text-muted-foreground line-clamp-1">
                      by {book.authors || "Unknown"}
                    </span>
                  </div>
                  <button 
                    onClick={() => toggleFavorite(book.title)}
                    className="p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.05] hover:bg-white/[0.08] hover:text-accent-pink hover:scale-105 active:scale-95 transition-all text-muted-foreground/80 shrink-0 cursor-pointer"
                  >
                    <Heart className={`w-3.5 h-3.5 transition-colors ${isFav ? "fill-accent-pink text-accent-pink" : ""}`} />
                  </button>
                </div>

                {/* Vibe and Trope badges */}
                <div className="flex flex-wrap gap-1 mt-0.5">
                  {book.soul?.reader_vibe && (
                    <span className="text-[9px] bg-accent-purple/10 border border-accent-purple/20 text-accent-purple px-2 py-0.5 rounded-full font-medium">
                      🧬 {book.soul.reader_vibe}
                    </span>
                  )}
                  {book.soul?.writing_style && (
                    <span className="text-[9px] bg-accent-pink/10 border border-accent-pink/20 text-accent-pink px-2 py-0.5 rounded-full font-medium">
                      ✍️ {book.soul.writing_style}
                    </span>
                  )}
                  {book.soul?.tropes?.slice(0, 2).map((trope) => (
                    <span key={trope} className="text-[9px] bg-accent-vibe/10 border border-accent-vibe/20 text-accent-vibe px-2 py-0.5 rounded-full font-medium">
                      {trope}
                    </span>
                  ))}
                </div>

                {/* Star rating placeholder */}
                <div className="flex items-center gap-1 text-[10px] text-accent-gold mt-auto pt-2">
                  <div className="flex gap-0.5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star key={i} className="w-2.5 h-2.5 fill-accent-gold" />
                    ))}
                  </div>
                  <span className="font-semibold text-muted-foreground/80">4.8</span>
                </div>

                {/* Accordion 1: Why This Matches */}
                <div className="border-t border-white/[0.05] pt-2.5 mt-1">
                  <button 
                    onClick={() => toggleMatchExplanation(bookId)}
                    className="flex justify-between items-center w-full text-[10px] font-bold text-accent-gold uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                  >
                    <span>Why it matches</span>
                    {isMatchExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>
                  
                  <AnimatePresence initial={false}>
                    {isMatchExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <p className="text-[11px] leading-relaxed text-muted-foreground/90 mt-2 font-sans font-light bg-white/[0.01] border border-white/[0.04] p-2.5 rounded-xl border-l-2 border-l-accent-purple">
                          {book.relevance_reason || (book.match_reasons && book.match_reasons[0]) || "This match aligns with your genres and preferred pacing structure."}
                        </p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Accordion 2: BookSoul DNA */}
                {book.soul?.dna && (
                  <div className="border-t border-white/[0.05] pt-2.5">
                    <button 
                      onClick={() => toggleDNAView(bookId)}
                      className="flex justify-between items-center w-full text-[10px] font-bold text-accent-purple uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                    >
                      <span>BookSoul DNA</span>
                      {isDNAExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                    
                    <AnimatePresence initial={false}>
                      {isDNAExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="flex flex-col gap-2 mt-2.5 p-2.5 bg-black/30 border border-white/[0.04] rounded-xl">
                            {[
                              { label: "Emotional Depth", val: book.soul.dna.emotional_depth },
                              { label: "Comfort", val: book.soul.dna.comfort },
                              { label: "Humor", val: book.soul.dna.humor },
                              { label: "Angst", val: book.soul.dna.angst },
                              { label: "Spice", val: book.soul.dna.spice },
                              { label: "Character Growth", val: book.soul.dna.character_growth },
                              { label: "Pacing", val: book.soul.dna.pacing },
                            ].map((row) => (
                              <div key={row.label} className="grid grid-cols-[80px_1fr_24px] items-center gap-2 text-[9px]">
                                <span className="text-muted-foreground text-left leading-none font-medium">{row.label}</span>
                                <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                                  <div 
                                    className="h-full bg-gradient-purple-pink rounded-full" 
                                    style={{ width: `${(row.val ?? 5) * 10}%` }}
                                  />
                                </div>
                                <span className="text-right text-foreground/80 font-bold">{row.val ?? 5}/10</span>
                              </div>
                            ))}
                            <div className="text-[9px] text-muted-foreground/70 border-t border-white/[0.05] pt-1.5 mt-0.5 leading-tight">
                              Atmosphere: <span className="text-accent-gold font-medium">{book.soul.dna.atmosphere || "Balanced"}</span>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function DiscoverPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex flex-col items-center justify-center p-12 min-h-[50vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="text-3xl animate-bounce">🔮</div>
          <span className="text-sm text-muted-foreground animate-pulse font-medium">Opening Catalog...</span>
        </div>
      </div>
    }>
      <DiscoverContent />
    </Suspense>
  );
}

import html
import re
import textwrap

import streamlit as st
from services.google_books import fetch_book_info
from services.booksoul_generator import generate_booksoul
from services.embeddings import store_book_vector, retrieve_book_vector
from services.recommender import get_semantic_recommendations, generate_recommendation_explanation
from services.comparator import compare_books, DIMENSIONS
from services.librarian import validate_book
from services.book_dna import ensure_book_dna, get_dna_values

# ---------------------------------------------------------------------------
# Genre maps for display-time soul field resolution
# ---------------------------------------------------------------------------
_GENRE_VIBE_MAP = {
    "romance": "Cozy Romance", "fantasy": "Magical & Immersive",
    "horror": "Dark & Thrilling", "mystery": "Suspenseful",
    "thriller": "High-Stakes Intense", "science fiction": "Futuristic",
    "sci-fi": "Futuristic & Speculative", "self": "Motivational & Reflective",
    "habit": "Motivational & Reflective", "history": "Thoughtful & Informative",
    "biography": "Thoughtful & Informative", "memoir": "Intimate & Raw",
    "young adult": "Coming-of-Age & Electric", "ya": "Coming-of-Age & Electric",
    "adventure": "Pulse-Pounding & Wild", "literary": "Deeply Introspective",
    "drama": "Emotionally Charged", "love": "Heart-Warming & Tender",
    "contemporary": "Grounded & Relatable", "classic": "Timeless & Profound",
    "comedy": "Lighthearted & Witty", "humor": "Playful & Sharp",
    "psychological": "Mind-Bending & Tense", "crime": "Gritty & Gripping",
    "dystopian": "Unsettling & Provocative", "philosophy": "Meditative & Enlightening",
    "sport": "Driven & Competitive", "cook": "Warm & Sensory",
    "travel": "Wanderlust & Free-Spirited", "graphic": "Visual & Dynamic",
    "fiction": "Emotionally Rich & Story-Driven",
}
_GENRE_STYLE_MAP = {
    "romance": "Character-Driven & Emotional", "fantasy": "World-Building & Descriptive",
    "horror": "Atmospheric & Dread-Soaked", "mystery": "Suspense-Driven & Layered",
    "thriller": "Fast-Paced & Gripping", "science fiction": "Concept-Driven & Speculative",
    "sci-fi": "Concept-Driven & Speculative", "self": "Practical & Actionable",
    "habit": "Practical & Actionable", "history": "Narrative Non-Fiction",
    "biography": "Narrative Non-Fiction", "memoir": "Confessional & Intimate",
    "young adult": "Voice-Driven & Visceral", "ya": "Voice-Driven & Visceral",
    "adventure": "Kinetic & Propulsive", "literary": "Lyrical & Deliberate",
    "drama": "Nuanced & Character-Focused", "love": "Sensory & Heartfelt",
    "contemporary": "Conversational & Authentic", "classic": "Elegant & Measured",
    "comedy": "Breezy & Witty", "humor": "Sharp & Irreverent",
    "psychological": "Unreliable & Twisting", "crime": "Terse & Investigative",
    "dystopian": "Bleak & Urgent", "philosophy": "Dense & Thought-Provoking",
    "fiction": "Immersive & Vividly Drawn",
}

def resolve_field(value, themes, genre_map, fallback):
    """Return value unless it is Unknown/N/A/empty, then infer from themes."""
    if value and value not in ("Unknown", "N/A", ""):
        return value
    text = " ".join(themes).lower()
    for keyword, label in genre_map.items():
        if keyword in text:
            return label
    return fallback


_TAG_RE = re.compile(r"<[^>]*>")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_display_text(value, fallback=""):
    """Normalize model/cache text so escaped HTML never reaches the UI as source."""
    if value is None:
        return fallback
    if isinstance(value, (list, tuple, set)):
        value = ", ".join(clean_display_text(item) for item in value if item)
    text = str(value)
    for _ in range(2):
        unescaped = html.unescape(text)
        if unescaped == text:
            break
        text = unescaped
    text = re.sub(r"(?i)<\s*br\s*/?\s*>", " ", text)
    text = re.sub(r"(?i)</\s*(p|div|li|span|strong|em|b|i)\s*>", " ", text)
    text = _TAG_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or fallback


def escape_display_text(value, fallback=""):
    return html.escape(clean_display_text(value, fallback), quote=True)


def render_badge(value, badge_type="trope", icon=""):
    label = escape_display_text(value)
    if not label:
        return ""
    badge_type = badge_type if badge_type in {"vibe", "style", "trope"} else "trope"
    prefix = f"{icon} " if icon else ""
    return f'<span class="badge badge-{badge_type}">{prefix}{label}</span>'


def render_badge_group(values, badge_type="trope", icon="", limit=None):
    if not values:
        return ""
    if not isinstance(values, (list, tuple, set)):
        values = [values]
    values = list(values)[:limit] if limit else list(values)
    return "".join(render_badge(value, badge_type, icon) for value in values)


def render_book_badges(soul, themes=None, trope_limit=4):
    """Return the shared visual badge HTML used by recommendation cards."""
    themes = themes or []
    vibe = resolve_field(
        soul.get("reader_vibe", ""),
        themes,
        _GENRE_VIBE_MAP,
        "Emotionally Resonant",
    )
    style = resolve_field(
        soul.get("writing_style", ""),
        themes,
        _GENRE_STYLE_MAP,
        "Richly Layered",
    )
    primary_badges = (
        render_badge(vibe, "vibe", "🧬")
        + render_badge(style, "style", "✍️")
    )
    trope_badges = render_badge_group(soul.get("tropes", []), "trope", limit=trope_limit)
    trope_group = f'<div style="margin-bottom:8px;">{trope_badges}</div>' if trope_badges else ""
    return f'<div style="margin-bottom:8px;">{primary_badges}</div>{trope_group}'


def render_book_dna(soul, description="", categories=None):
    if not isinstance(soul, dict):
        soul = {}
    ensure_book_dna(soul, description=description, categories=categories)
    dna_values = get_dna_values(soul.get("dna", {}))
    if not dna_values.get("atmosphere"):
        dna_values["atmosphere"] = clean_display_text(
            soul.get("emotional_tone") or soul.get("reader_vibe") or "Balanced",
            "Balanced",
        )
    dna_labels = {
        "emotional_depth": "Emotional Depth",
        "comfort": "Comfort",
        "humor": "Humor",
        "angst": "Angst",
        "spice": "Spice",
        "character_growth": "Character Growth",
        "pacing": "Pacing",
    }
    rows = []
    for key, label in dna_labels.items():
        filled = int(max(0, min(10, dna_values.get(key, 5))))
        rows.append(
            '<div class="dna-row">'
            f'<span class="dna-label">{escape_display_text(label)}</span>'
            '<span class="dna-track">'
            f'<span class="dna-fill" style="width:{filled * 10}%;"></span>'
            '</span>'
            f'<span class="dna-score">{filled}/10</span>'
            '</div>'
        )
    atmosphere = escape_display_text(dna_values.get("atmosphere", "Balanced"))
    return (
        '<div class="dna-panel">'
        '<div class="dna-title">BookSoul DNA</div>'
        f'{"".join(rows)}'
        f'<div class="dna-atmosphere">Atmosphere: {atmosphere}</div>'
        '</div>'
    )

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="BookSoul · AI Book Recommender",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# GLOBAL CSS — Dark Glassmorphism Theme
# ============================================================
st.markdown("""
<style>
/* ── Google Font ──────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

/* ── Root Variables ───────────────────────────────────────── */
:root {
  --bg:          #0d0f14;
  --surface:     #13161e;
  --glass:       rgba(255,255,255,0.04);
  --glass-hover: rgba(255,255,255,0.07);
  --border:      rgba(255,255,255,0.08);
  --accent1:     #a78bfa;   /* violet */
  --accent2:     #f472b6;   /* pink */
  --accent3:     #34d399;   /* emerald */
  --text-primary:#f1f5f9;
  --text-muted:  #94a3b8;
  --radius:      16px;
  --shadow:      0 8px 32px rgba(0,0,0,0.45);
}

/* ── Base ─────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: 'Inter', sans-serif !important;
  color: var(--text-primary) !important;
}

[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 20% 10%, rgba(167,139,250,0.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 80%, rgba(244,114,182,0.10) 0%, transparent 55%);
  pointer-events: none;
  z-index: 0;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; }
[data-testid="block-container"] { padding-top: 2rem !important; }

/* ── Typography ───────────────────────────────────────────── */
h1, h2, h3, h4 {
  font-family: 'Playfair Display', serif !important;
  color: var(--text-primary) !important;
}
p, li, label, span, div {
  color: var(--text-primary) !important;
}
.stMarkdown p { color: var(--text-muted) !important; }

/* ── Tabs ─────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 50px;
  padding: 4px;
  gap: 4px;
  backdrop-filter: blur(12px);
}
[data-testid="stTabs"] [role="tab"] {
  border-radius: 50px !important;
  color: var(--text-muted) !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
  padding: 8px 24px !important;
  transition: all 0.2s ease !important;
  border: none !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, var(--accent1), var(--accent2)) !important;
  color: white !important;
  box-shadow: 0 2px 12px rgba(167,139,250,0.4) !important;
}
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {
  background: var(--glass-hover) !important;
  color: var(--text-primary) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTabs"] [data-baseweb="tab-border"]    { display: none !important; }

/* ── Inputs ───────────────────────────────────────────────── */
[data-testid="stTextInput"] input {
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--text-primary) !important;
  font-size: 1rem !important;
  padding: 14px 18px !important;
  backdrop-filter: blur(8px);
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: var(--accent1) !important;
  box-shadow: 0 0 0 3px rgba(167,139,250,0.2) !important;
  outline: none !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--text-muted) !important; }
[data-testid="stTextInput"] label {
  color: var(--text-muted) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.03em !important;
}

/* ── Buttons ──────────────────────────────────────────────── */
[data-testid="stButton"] button {
  background: linear-gradient(135deg, var(--accent1) 0%, var(--accent2) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 50px !important;
  font-weight: 600 !important;
  font-size: 0.95rem !important;
  padding: 12px 32px !important;
  cursor: pointer !important;
  transition: all 0.25s ease !important;
  box-shadow: 0 4px 20px rgba(167,139,250,0.35) !important;
  letter-spacing: 0.02em !important;
}
[data-testid="stButton"] button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 28px rgba(167,139,250,0.5) !important;
  filter: brightness(1.1) !important;
}
[data-testid="stButton"] button:active {
  transform: translateY(0) !important;
}

/* ── Spinner ──────────────────────────────────────────────── */
[data-testid="stSpinner"] { color: var(--accent1) !important; }

/* ── Success / Warning / Error / Info ─────────────────────── */
[data-testid="stAlert"] {
  border-radius: 12px !important;
  border: none !important;
  backdrop-filter: blur(8px) !important;
}
[data-testid="stAlert"][data-baseweb="notification"] {
  background: rgba(52,211,153,0.1) !important;
  border-left: 3px solid var(--accent3) !important;
}

/* ── Expander ─────────────────────────────────────────────── */
[data-testid="stExpander"] {
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  backdrop-filter: blur(8px) !important;
}

/* ── Code blocks ──────────────────────────────────────────── */
[data-testid="stCode"] {
  background: rgba(0,0,0,0.35) !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
}

/* ── Dividers ─────────────────────────────────────────────── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.5rem 0 !important;
}

/* ── Book card (custom HTML component) ───────────────────────*/
.book-card {
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  margin-bottom: 1.2rem;
  backdrop-filter: blur(12px);
  transition: border-color 0.25s, box-shadow 0.25s, transform 0.2s;
  box-shadow: var(--shadow);
  animation: slideUp 0.4s ease both;
}
.book-card:hover {
  border-color: rgba(167,139,250,0.4);
  box-shadow: 0 12px 40px rgba(167,139,250,0.15);
  transform: translateY(-3px);
}

/* ── Badge chips ──────────────────────────────────────────── */
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 50px;
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  margin: 2px 3px;
}
.badge-vibe  { background: rgba(167,139,250,0.18); color: #c4b5fd; border: 1px solid rgba(167,139,250,0.3); }
.badge-style { background: rgba(244,114,182,0.15); color: #f9a8d4; border: 1px solid rgba(244,114,182,0.3); }
.badge-trope { background: rgba(52,211,153,0.12);  color: #6ee7b7; border: 1px solid rgba(52,211,153,0.25); }

/* ── Match reason box ─────────────────────────────────────── */
.match-reason {
  background: linear-gradient(135deg, rgba(167,139,250,0.08), rgba(244,114,182,0.06));
  border-left: 3px solid var(--accent1);
  border-radius: 0 10px 10px 0;
  padding: 10px 14px;
  margin-top: 10px;
  font-size: 0.88rem;
  color: var(--text-muted) !important;
  line-height: 1.6;
}

/* ── Rank number ──────────────────────────────────────────── */
.rank-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px; height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent1), var(--accent2));
  color: white;
  font-weight: 700;
  font-size: 0.85rem;
  margin-right: 8px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(167,139,250,0.4);
}

/* ── Soul Match bar ───────────────────────────────────────── */
.soul-match-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0 14px;
}
.soul-match-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent1);
  white-space: nowrap;
}
.soul-match-bar-bg {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 99px;
  overflow: hidden;
}
.soul-match-bar-fill {
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, var(--accent1), var(--accent2));
  transition: width 0.6s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 0 8px rgba(167,139,250,0.5);
}
.soul-match-pct {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent1);
  min-width: 38px;
  text-align: right;
}

.dna-panel {
  margin: 12px 0 10px;
  padding: 12px 14px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  background: rgba(0,0,0,0.16);
}
.dna-title {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent1);
  margin-bottom: 8px;
}
.dna-row {
  display: grid;
  grid-template-columns: minmax(120px, 170px) 1fr 42px;
  align-items: center;
  gap: 10px;
  margin: 5px 0;
}
.dna-label {
  color: var(--text-muted);
  font-size: 0.78rem;
}
.dna-track {
  height: 6px;
  border-radius: 99px;
  background: rgba(255,255,255,0.08);
  overflow: hidden;
}
.dna-fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, var(--accent1), var(--accent2));
}
.dna-score {
  color: var(--text-primary);
  font-size: 0.76rem;
  font-weight: 600;
  text-align: right;
}
.dna-atmosphere {
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 0.8rem;
}

/* ── AI Thinking animation ────────────────────────────────── */
@keyframes aiPulse {
  0%, 100% { opacity: 0.4; transform: scale(0.9); }
  50%       { opacity: 1;   transform: scale(1.05); }
}
.ai-thinking {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  color: var(--accent1);
  padding: 4px 12px;
  background: rgba(167,139,250,0.08);
  border: 1px solid rgba(167,139,250,0.2);
  border-radius: 50px;
  margin-bottom: 10px;
}
.ai-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--accent1);
  animation: aiPulse 1.2s ease infinite;
}
.ai-dot:nth-child(2) { animation-delay: 0.2s; }
.ai-dot:nth-child(3) { animation-delay: 0.4s; }

/* ── Book description excerpt ─────────────────────────────── */
.book-desc {
  font-size: 0.85rem;
  color: var(--text-muted) !important;
  line-height: 1.7;
  margin-top: 10px;
  border-top: 1px solid var(--border);
  padding-top: 10px;
}

/* ── No-cover placeholder ─────────────────────────────────── */
.no-cover {
  width: 100%;
  aspect-ratio: 2/3;
  background: linear-gradient(135deg, rgba(167,139,250,0.15), rgba(244,114,182,0.1));
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
}

/* ── Slide-up animation ───────────────────────────────────── */
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0);    }
}

/* ── Hero header ──────────────────────────────────────────── */
.hero {
  text-align: center;
  padding: 2.5rem 1rem 1.5rem;
  animation: slideUp 0.5s ease;
}
.hero-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2.2rem, 5vw, 3.5rem);
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa 0%, #f472b6 50%, #34d399 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.15;
  margin-bottom: 0.5rem;
}
.hero-sub {
  color: var(--text-muted) !important;
  font-size: 1.05rem;
  font-weight: 300;
  letter-spacing: 0.04em;
  margin: 0;
}

/* ── Section labels ───────────────────────────────────────── */
.section-label {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent1) !important;
  margin-bottom: 0.5rem;
}

/* ── Stat strip ───────────────────────────────────────────── */
.stat-strip {
  display: flex;
  gap: 1.5rem;
  padding: 0.8rem 1.2rem;
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: 50px;
  margin-bottom: 1.5rem;
  backdrop-filter: blur(10px);
  flex-wrap: wrap;
}
.stat-item { font-size: 0.82rem; color: var(--text-muted) !important; }
.stat-item strong { color: var(--text-primary) !important; }

/* ── Ingest metadata table ────────────────────────────────── */
.meta-row {
  display: flex;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.88rem;
}
.meta-key   { color: var(--text-muted) !important; min-width: 130px; font-weight: 500; }
.meta-value { color: var(--text-primary) !important; }

/* ── Onboarding ───────────────────────────────────────────── */
.onboard-wrap {
  max-width: 760px;
  margin: 0 auto;
  padding: 2rem 1rem 4rem;
  animation: slideUp 0.5s ease;
}
.onboard-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2rem, 4.5vw, 3rem);
  font-weight: 700;
  background: linear-gradient(135deg, #a78bfa 0%, #f472b6 50%, #34d399 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: center;
  margin-bottom: 0.4rem;
  line-height: 1.2;
}
.onboard-sub {
  text-align: center;
  color: var(--text-muted) !important;
  font-size: 1rem;
  margin-bottom: 2.5rem;
}
.onboard-step {
  background: var(--glass);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.6rem 1.8rem;
  margin-bottom: 1.2rem;
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow);
}
.onboard-step-title {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent1) !important;
  margin-bottom: 0.8rem;
}
.onboard-step h3 {
  font-family: 'Inter', sans-serif !important;
  font-size: 1.05rem !important;
  font-weight: 600 !important;
  margin: 0 0 1rem 0 !important;
  color: var(--text-primary) !important;
}
.content-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.content-option {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.content-option:hover {
  border-color: rgba(167,139,250,0.4);
  background: rgba(167,139,250,0.06);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ONBOARDING GATE
# Show once per session; stores profile in session_state
# ============================================================
if "onboarding_done" not in st.session_state:

    st.markdown('<div class="onboard-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="onboard-title">📚 Welcome to BookSoul</div>
    <p class="onboard-sub">Before we find stories you'll love, tell us a little about yourself.</p>
    """, unsafe_allow_html=True)

    # ── Step 1: Age group ─────────────────────────────────────
    st.markdown('<div class="onboard-step">', unsafe_allow_html=True)
    st.markdown('<p class="onboard-step-title">Step 1 of 4 · Age Group</p>', unsafe_allow_html=True)
    age_group = st.radio(
        "Which age group best describes you?",
        options=["👧 Under 13", "🧒 13–15", "🧑 16–17", "👩 18–24", "👨 25–34", "👵 35+"],
        index=3,
        key="ob_age",
        help="Helps us recommend age-appropriate books."
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Step 2: Content level ─────────────────────────────────
    st.markdown('<div class="onboard-step">', unsafe_allow_html=True)
    st.markdown('<p class="onboard-step-title">Step 2 of 4 · Content Comfort</p>', unsafe_allow_html=True)
    content_level = st.radio(
        "Which content are you comfortable reading?",
        options=[
            "🌼 Family Friendly — No explicit content, minimal violence",
            "💕 Mild Romance — Kissing & romance, fade-to-black only",
            "❤️ Mature Romance — Explicit romance (spice), adult readers"
        ],
        index=1,
        key="ob_content"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Step 3: Genres ────────────────────────────────────────
    st.markdown('<div class="onboard-step">', unsafe_allow_html=True)
    st.markdown('<p class="onboard-step-title">Step 3 of 4 · Favourite Genres</p>', unsafe_allow_html=True)
    st.markdown("<p style='color:var(--text-muted);font-size:0.88rem;margin-bottom:0.8rem;'>Select all that apply.</p>", unsafe_allow_html=True)
    _GENRES = [
        "Romance", "Fantasy", "Mystery", "Thriller",
        "Historical Fiction", "Science Fiction", "Horror",
        "Literary Fiction", "Young Adult", "Non-fiction",
        "Biography", "Self-help", "Other"
    ]
    genre_cols = st.columns(3)
    selected_genres = []
    for i, g in enumerate(_GENRES):
        with genre_cols[i % 3]:
            if st.checkbox(g, key=f"ob_genre_{g}"):
                selected_genres.append(g)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Step 4: Free-text mood ────────────────────────────────
    st.markdown('<div class="onboard-step">', unsafe_allow_html=True)
    st.markdown('<p class="onboard-step-title">Step 4 of 4 · What Are You Looking For?</p>', unsafe_allow_html=True)
    free_text = st.text_input(
        label="mood_query",
        label_visibility="collapsed",
        placeholder='e.g. "A slow-burn romance" · "Books like Wild Love" · "Cozy fantasy"',
        key="ob_free"
    )
    st.markdown("""
    <p style='color:var(--text-muted);font-size:0.8rem;margin-top:0.5rem;'>
    💡 This becomes your first search — you can always change it later.
    </p>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Submit ────────────────────────────────────────────────
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    _, ctr, _ = st.columns([2, 3, 2])
    with ctr:
        if st.button("✨ Start Discovering →", key="ob_submit", use_container_width=True):
            st.session_state["profile"] = {
                "age_group":     age_group,
                "content_level": content_level,
                "genres":        selected_genres if selected_genres else ["Any"],
                "mood_query":    free_text.strip()
            }
            st.session_state["onboarding_done"] = True
            # Pre-fill the recommendation search with their mood query
            if free_text.strip():
                st.session_state["rec_input"] = free_text.strip()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()   # ← Don't render anything below until onboarding is complete

# ============================================================
# HERO HEADER  (shown only after onboarding)
# ============================================================
profile = st.session_state.get("profile", {})
st.markdown("""
<div class="hero">
  <div class="hero-title">📚 BookSoul</div>
  <p class="hero-sub">Discover your next read through narrative DNA &amp; semantic search</p>
</div>
""", unsafe_allow_html=True)

# ── Personalised profile strip ────────────────────────────────
if profile:
    genre_str   = " · ".join(profile.get("genres", [])[:4])
    content_str = profile.get("content_level", "").split("—")[0].strip()
    age_str     = profile.get("age_group", "")
    st.markdown(f"""
    <div class="stat-strip" style="justify-content:center;margin-bottom:1rem;">
      <span class="stat-item">👤 <strong>{age_str}</strong></span>
      <span class="stat-item">📖 <strong>{content_str}</strong></span>
      <span class="stat-item">🎭 <strong>{genre_str if genre_str else 'All genres'}</strong></span>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3 = st.tabs(["✦ Find Recommendations", "⚖️ Compare Books", "⊕ Add Books to DB"])

# ============================================================
# TAB 2 — COMPARE BOOKS
# ============================================================
with tab2:
    st.markdown('<p class="section-label">Compare two books side by side</p>', unsafe_allow_html=True)

    col_b1, col_vs, col_b2 = st.columns([5, 1, 5])
    with col_b1:
        cmp_q1 = st.text_input(
            label="book1_query",
            label_visibility="collapsed",
            placeholder="Book 1 — e.g. Harry Potter",
            key="cmp_input1"
        )
    with col_vs:
        st.markdown(
            '<div style="text-align:center;padding-top:14px;font-size:1.3rem;'
            'font-weight:700;color:#a78bfa;">VS</div>',
            unsafe_allow_html=True
        )
    with col_b2:
        cmp_q2 = st.text_input(
            label="book2_query",
            label_visibility="collapsed",
            placeholder="Book 2 — e.g. Percy Jackson",
            key="cmp_input2"
        )

    cmp_clicked = st.button("⚖️ Compare Now", key="cmp_btn")

    if cmp_clicked:
        if not cmp_q1.strip() or not cmp_q2.strip():
            st.warning("Please enter both book titles to compare.")
        else:
            with st.spinner("📚 Fetching books and analysing literary DNA..."):
                result = compare_books(cmp_q1.strip(), cmp_q2.strip())

            if "error" in result:
                st.error(result["error"])
            else:
                b1   = result["book1"]
                b2   = result["book2"]
                soul1 = result["soul1"]
                soul2 = result["soul2"]
                scores = result["scores"]
                summary = result["summary"]

                # ── Book header cards ──────────────────────────
                hdr1, hdr2 = st.columns(2, gap="large")
                for hdr_col, book, soul in [(hdr1, b1, soul1), (hdr2, b2, soul2)]:
                    with hdr_col:
                        cover_url = escape_display_text(book.get("cover_image", ""))
                        cover_html = (
                            f'<img src="{cover_url}" '
                            'style="width:90px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.5);margin-bottom:10px;">'
                            if cover_url else
                            '<div class="no-cover" style="width:90px;height:135px;font-size:2rem;">📖</div>'
                        )
                        authors_str = escape_display_text(book.get("authors", []), "Unknown")
                        st.markdown(f"""
                        <div class="book-card" style="text-align:center;">
                          <div style="display:flex;justify-content:center;margin-bottom:8px;">{cover_html}</div>
                          <div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;margin-bottom:4px;">{escape_display_text(book.get('title', 'Untitled'))}</div>
                          <div style="color:#94a3b8;font-size:0.85rem;margin-bottom:10px;">by {authors_str}</div>
                          <div>
                            {render_badge(soul.get('reader_vibe', 'N/A'), 'vibe', '🧬')}
                            {render_badge(soul.get('writing_style', 'N/A'), 'style', '✍️')}
                            {render_badge(soul.get('emotional_tone', 'N/A'), 'trope', '🎭')}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown('<hr>', unsafe_allow_html=True)
                st.markdown('<p class="section-label" style="text-align:center;">Literary DNA Comparison</p>', unsafe_allow_html=True)

                # ── Dimension rows ─────────────────────────────
                for dim_score in scores:
                    name   = dim_score["name"]
                    icon   = dim_score["icon"]
                    s1     = dim_score["score1"]
                    s2     = dim_score["score2"]
                    d_type = dim_score["type"]

                    def render_pips(score, pip_type, align="left"):
                        if pip_type == "pepper":
                            filled = "🌶️" * score
                            empty  = "<span style='opacity:0.25'>🌶️</span>" * (5 - score)
                        else:
                            filled = "⭐" * score
                            empty  = "<span style='opacity:0.25'>⭐</span>" * (5 - score)
                        if align == "right":
                            return empty + filled
                        return filled + empty

                    win1_style = "color:#a78bfa;font-weight:700" if s1 > s2 else "color:#94a3b8"
                    win2_style = "color:#a78bfa;font-weight:700" if s2 > s1 else "color:#94a3b8"

                    row_l, row_c, row_r = st.columns([4, 3, 4])
                    with row_l:
                        st.markdown(
                            f'<div style="text-align:right;padding:6px 0;{win1_style}">'
                            f'{render_pips(s1, d_type, "right")}&nbsp;&nbsp;<strong>{s1}/5</strong></div>',
                            unsafe_allow_html=True
                        )
                    with row_c:
                        st.markdown(
                            f'<div style="text-align:center;padding:6px 0;font-weight:600;">'
                            f'{icon} {name}</div>',
                            unsafe_allow_html=True
                        )
                    with row_r:
                        st.markdown(
                            f'<div style="text-align:left;padding:6px 0;{win2_style}">'
                            f'<strong>{s2}/5</strong>&nbsp;&nbsp;{render_pips(s2, d_type)}</div>',
                            unsafe_allow_html=True
                        )

                # ── Verdict ────────────────────────────────────
                st.markdown('<hr>', unsafe_allow_html=True)
                wins1 = summary["wins1"]
                wins2 = summary["wins2"]

                v_col1, v_col2, v_col3 = st.columns([3, 4, 3])
                with v_col1:
                    st.markdown(
                        f'<div class="book-card" style="text-align:center;">'
                        f'<div style="font-size:1.8rem;font-weight:700;color:#a78bfa;">{wins1}</div>'
                        f'<div style="color:#94a3b8;font-size:0.82rem;">categories won</div>'
                        f'<div style="font-size:0.85rem;margin-top:4px;font-weight:600;">{b1["title"][:25]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with v_col2:
                    st.markdown(
                        f'<div class="book-card" style="text-align:center;padding:1.5rem;">'
                        f'<div style="font-size:1.1rem;line-height:1.6;">{summary["verdict"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with v_col3:
                    st.markdown(
                        f'<div class="book-card" style="text-align:center;">'
                        f'<div style="font-size:1.8rem;font-weight:700;color:#f472b6;">{wins2}</div>'
                        f'<div style="color:#94a3b8;font-size:0.82rem;">categories won</div>'
                        f'<div style="font-size:0.85rem;margin-top:4px;font-weight:600;">{b2["title"][:25]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

# ============================================================
# TAB 1 — RECOMMENDATIONS
# ============================================================
with tab1:
    st.markdown('<p class="section-label">What are you in the mood for?</p>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        recommend_query = st.text_input(
            label="search_query",
            label_visibility="collapsed",
            placeholder="e.g.  cozy workplace romance with slow burn tension  ·  dark academia mystery  ·  books like Wild Love",
            key="rec_input"
        )
    with col_btn:
        search_clicked = st.button("🔍 Search", key="search_btn", use_container_width=True)

    if search_clicked and recommend_query:
        # AI thinking animation while loading
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown(
            '<div class="ai-thinking">'
            '<div class="ai-dot"></div><div class="ai-dot"></div><div class="ai-dot"></div>'
            '&nbsp; BookSoul is thinking…'
            '</div>',
            unsafe_allow_html=True
        )
        with st.spinner("Consulting the AI Librarian..."):
            matches = get_semantic_recommendations(recommend_query, n_results=5)
        thinking_placeholder.empty()

        if matches:
            st.markdown(f"""
            <div class="stat-strip">
              <span class="stat-item">🎯 Found <strong>{len(matches)}</strong> matches</span>
              <span class="stat-item">🔎 Query: <strong>{escape_display_text(recommend_query)}</strong></span>
              <span class="stat-item">📡 Source: internet + vector DB</span>
            </div>
            """, unsafe_allow_html=True)

            for index, match in enumerate(matches, 1):
                soul          = match.get("soul", {})
                themes        = soul.get("themes", [])
                soul_match    = match.get("soul_match", 0)          # normalised 0–100%
                match_reasons = match.get("match_reasons", [])
                description   = match.get("description", "")

                try:
                    soul_match = max(0, min(100, int(float(soul_match))))
                except (TypeError, ValueError):
                    soul_match = 0
                title = escape_display_text(match.get("title", "Untitled"))
                authors = escape_display_text(match.get("authors", "Unknown author"))
                badge_html = render_book_badges(soul, themes)
                dna_html = render_book_dna(soul, description=description, categories=themes)

                # Soul Match colour: green ≥75, amber 55–74, violet <55
                if soul_match >= 75:
                    bar_color = "linear-gradient(90deg,#34d399,#6ee7b7)"
                elif soul_match >= 55:
                    bar_color = "linear-gradient(90deg,#f59e0b,#fcd34d)"
                else:
                    bar_color = "linear-gradient(90deg,#a78bfa,#f472b6)"

                soul_bar_html = (
                    '<div class="soul-match-wrap">'
                    '<span class="soul-match-label">Soul Match</span>'
                    '<div class="soul-match-bar-bg">'
                    f'<div class="soul-match-bar-fill" style="width:{soul_match}%;background:{bar_color};"></div>'
                    '</div>'
                    f'<span class="soul-match-pct">{soul_match}%</span>'
                    '</div>'
                )

                clean_description = clean_display_text(description)
                desc_excerpt = clean_description[:280] + "…" if len(clean_description) > 280 else clean_description
                desc_html = escape_display_text(desc_excerpt)

                col_cover, col_info = st.columns([1, 4], gap="medium")

                with col_cover:
                    if match.get("cover_image"):
                        st.image(match["cover_image"], use_container_width=True)
                    else:
                        st.markdown('<div class="no-cover">📖</div>', unsafe_allow_html=True)

                with col_info:
                    # ── Card: Title + Author + Soul Match bar ──────────────
                    st.markdown(textwrap.dedent(f"""
                    <div class="book-card">
                      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                        <span class="rank-num">{index}</span>
                        <span style="font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;color:#f1f5f9;">{title}</span>
                      </div>
                      <div style="color:#94a3b8;font-size:0.85rem;margin-bottom:4px;">by {authors}</div>

                      {soul_bar_html}

                      {badge_html}

                      {dna_html}

                      {f'<div class="book-desc">{desc_html}</div>' if desc_html else ''}
                    </div>
                    """), unsafe_allow_html=True)

                    # ── Why BookSoul picked this ───────────────────────────
                    if match_reasons:
                        reasons_html = "".join(
                            f'<div style="padding:3px 0;font-size:0.85rem;color:#c4b5fd;">'
                            f'{escape_display_text(r)}</div>' for r in match_reasons
                        )
                        st.markdown(
                            f'<div class="match-reason">'
                            f'<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;'
                            f'text-transform:uppercase;color:#a78bfa;margin-bottom:6px;">'
                            f'✨ Why BookSoul Picked This</div>'
                            f'{reasons_html}</div>',
                            unsafe_allow_html=True
                        )

                st.markdown("<hr>", unsafe_allow_html=True)

        elif search_clicked:
            st.warning("No matches found. Try a different query — the internet search will fetch new books automatically.")

# ============================================================
# TAB 3 — INGEST (Fixed Flow State)
# ============================================================
with tab3:
    st.markdown('<p class="section-label">Manually add a book to your library</p>', unsafe_allow_html=True)

    search_query = st.text_input(
        label="ingest_query",
        label_visibility="collapsed",
        placeholder="e.g.  Wild Love by Elsie Silver  ·  Atomic Habits by James Clear",
        key="ingest_input"
    )

    # Trigger fetch and cache result — spinner runs inside button block
    if st.button("📖 Fetch from Google Books", key="fetch_btn") and search_query:
        with st.spinner("Fetching from Google Books..."):
            book = fetch_book_info(search_query)
            if book:
                is_valid, score, reason = validate_book(book)
                if not is_valid:
                    st.error(f"⚠️ **Rejected by Librarian:** {reason}")
                else:
                    st.session_state["fetched_book"] = book
                    st.session_state["fetched_book_score"] = score
                    # Flush stale soul data from any previous book lookup
                    for _k in ("current_soul", "current_book"):
                        if _k in st.session_state:
                            del st.session_state[_k]
            else:
                st.error("No book found for that query. Try including the author name.")

    # ── Stage 1: Book card — persists independently of fetch button ───────────
    if "fetched_book" in st.session_state:
        book = st.session_state["fetched_book"]
        fetched_cover = escape_display_text(book.get("cover_image", ""))
        fetched_description = clean_display_text(book.get("description", ""))
        fetched_description = fetched_description[:400] + "..." if len(fetched_description) > 400 else fetched_description
        st.markdown(f"""
        <div class="book-card" style="margin-top:1rem;">
          <div style="display:flex;gap:1.5rem;align-items:flex-start;">
            <div style="flex-shrink:0;">
              {'<img src="' + fetched_cover + '" style="width:110px;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.5);">' if fetched_cover else '<div class="no-cover" style="width:110px;">📖</div>'}
            </div>
            <div>
              <div style="font-family:\'Playfair Display\',serif;font-size:1.4rem;font-weight:700;margin-bottom:4px;">{escape_display_text(book.get('title', 'Untitled'))}</div>
              <div class="meta-row"><span class="meta-key">Author(s)</span><span class="meta-value">{escape_display_text(book.get("authors", []))}</span></div>
              <div class="meta-row"><span class="meta-key">Published</span><span class="meta-value">{escape_display_text(book.get("published_year", ""))}</span></div>
              <div class="meta-row"><span class="meta-key">Categories</span><span class="meta-value">{escape_display_text(book.get("categories", []))}</span></div>
            </div>
          </div>
          <div style="margin-top:1rem;color:#94a3b8;font-size:0.88rem;line-height:1.6;">{escape_display_text(fetched_description)}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p class="section-label" style="margin-top:1.5rem;">Extract Narrative DNA</p>', unsafe_allow_html=True)

        # Top-level button — NOT nested inside fetch block, survives re-renders
        if st.button("✨ Generate BookSoul via Gemini", key="soul_btn"):
            with st.spinner("Gemini is reading between the lines..."):
                soul_json = generate_booksoul(book["title"], book.get("description", ""), ", ".join(book.get("categories", [])))
            if "error" in soul_json:
                st.error(soul_json["error"])
            else:
                st.session_state["current_soul"] = soul_json
                st.session_state["current_book"] = book

    # ── Stage 2: Soul card — persists independently of soul button ────────────
    if "current_soul" in st.session_state:
        soul = st.session_state["current_soul"]
        book = st.session_state.get("current_book", {})
        themes_display = soul.get("themes", [])
        tropes_display = soul.get("tropes", [])
        dna_html = render_book_dna(
            soul,
            description=book.get("description", ""),
            categories=book.get("categories", themes_display),
        )

        st.markdown(f"""
        <div class="book-card" style="margin-top:0.5rem;">
          <div style="font-family:'Playfair Display',serif;font-size:1rem;font-weight:600;margin-bottom:12px;color:#a78bfa;">🧬 BookSoul Generated</div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;">
            {render_badge('Vibe: ' + clean_display_text(soul.get('reader_vibe', 'N/A')), 'vibe')}
            {render_badge('Style: ' + clean_display_text(soul.get('writing_style', 'N/A')), 'style')}
            {render_badge('Tone: ' + clean_display_text(soul.get('emotional_tone', 'N/A')), 'trope')}
            {render_badge('Pacing: ' + clean_display_text(soul.get('pacing', 'N/A')), 'trope')}
          </div>
          <div>{render_badge_group(tropes_display, 'trope')}</div>
          <div style="margin-top:8px;">{render_badge_group(themes_display, 'vibe')}</div>
          {dna_html}
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p class="section-label" style="margin-top:1.5rem;">Save to Vector Database</p>', unsafe_allow_html=True)

        book_title = st.session_state["current_book"]["title"]
        book_id = "".join(e for e in book_title if e.isalnum()).lower()

        if st.button("💾 Save to ChromaDB", key="save_btn"):
            with st.spinner("Embedding narrative text and indexing into ChromaDB..."):
                success = store_book_vector(
                    book_id=book_id,
                    book_title=book_title,
                    book_metadata=st.session_state["current_book"],
                    soul_json=st.session_state["current_soul"],
                    quality_score=st.session_state.get("fetched_book_score", 0)
                )
            if success:
                st.success(f"✅ '{book_title}' is now in your vector library!")
                with st.spinner("Verifying DB record..."):
                    retrieved = retrieve_book_vector(book_id)
                if retrieved:
                    with st.expander("📦 View stored vector payload"):
                        st.code(retrieved["document"], language="text")
            else:
                st.error("Failed to write to ChromaDB.")

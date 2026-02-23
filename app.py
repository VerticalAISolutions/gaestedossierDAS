"""
Streamlit Frontend für das Gästedossier-Tool.
Starten mit: streamlit run app.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

import streamlit as st

# Projekt-Root
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# Streamlit Cloud: Secrets in os.environ übertragen,
# damit os.getenv() in den Tools funktioniert
try:
    for _key, _val in st.secrets.items():
        if isinstance(_val, str):
            os.environ.setdefault(_key, _val)
except Exception:
    pass

sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from research_guest import run_research, disambiguate_guest, slugify
from create_dossier import create_dossier

# --- Page Config ---
st.set_page_config(
    page_title="DAS! Gästedossier",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Styles aus styles.css laden + Streamlit-spezifische Overrides ---
css_path = PROJECT_ROOT / "styles.css"
base_css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

st.markdown(f"""
<style>
{base_css}

/* === Streamlit Overrides === */

/* Reset Streamlit defaults to match styles.css */
.stApp {{
    background-color: #FAFAF9;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

section[data-testid="stSidebar"] {{
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}}

section[data-testid="stSidebar"] .stMarkdown h2 {{
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #4b5563;
    margin-bottom: 0.75rem;
}}

/* Header */
.app-header {{
    padding: 1rem 0 0.5rem 0;
    margin-bottom: 1rem;
}}

.app-title {{
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    color: #111827;
    line-height: 1.2;
    margin: 0;
}}

.app-subtitle {{
    font-size: 0.875rem;
    line-height: 1.75;
    color: #4b5563;
    margin-top: 0.25rem;
}}

/* Global content width */
.stMainBlockContainer {{
    max-width: 75% !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}

/* Guest identity card */
.identity-card {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
}}

.identity-card h3 {{
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
    margin: 0 0 0.25rem 0;
}}

.identity-card p {{
    font-size: 0.875rem;
    color: #4b5563;
    margin: 0;
}}

/* Disambiguation cards */
.disambig-card {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.15s ease;
}}

.disambig-card:hover {{
    border-color: #9ca3af;
}}

.disambig-card h4 {{
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
    margin: 0 0 0.25rem 0;
}}

.disambig-card p {{
    font-size: 0.875rem;
    color: #4b5563;
    margin: 0;
}}

/* Pipeline steps */
.pipeline-step {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
}}

.pipeline-step-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}}

.step-number {{
    width: 2rem;
    height: 2rem;
    border-radius: 9999px;
    background-color: #111827;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 600;
    flex-shrink: 0;
}}

.step-number.done {{
    background-color: #16a34a;
}}

.step-number.active {{
    background-color: #111827;
    animation: pulse-ring 1.5s ease-in-out infinite;
}}

.step-title {{
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
}}

/* Pulsing animation for active step */
@keyframes pulse-ring {{
    0% {{ box-shadow: 0 0 0 0 rgba(17, 24, 39, 0.3); }}
    50% {{ box-shadow: 0 0 0 8px rgba(17, 24, 39, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(17, 24, 39, 0); }}
}}

/* Animated progress bar */
@keyframes shimmer {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}

.active-progress {{
    width: 100%;
    height: 4px;
    border-radius: 2px;
    background: linear-gradient(90deg, #e5e7eb 25%, #9ca3af 50%, #e5e7eb 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    margin: 0.75rem 0;
}}

/* Dossier result */
.dossier-result {{
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 2rem;
    margin-top: 1.5rem;
}}

/* Research data uniform font */
.research-data-view,
.research-data-view h1,
.research-data-view h2,
.research-data-view h3,
.research-data-view h4,
.research-data-view p,
.research-data-view li,
.research-data-view strong,
.research-data-view em,
.research-data-view a,
.research-data-view span {{
    font-size: 0.875rem !important;
    line-height: 1.6 !important;
}}

.research-data-view h1,
.research-data-view h2,
.research-data-view h3 {{
    font-weight: 600 !important;
    color: #111827;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    border: none !important;
    padding: 0 !important;
}}

/* h1 = Hauptabschnitte: THE CHEAT SHEET, HIDDEN GEMS, etc. */
.dossier-result h1 {{
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: #111827;
    margin-top: 4rem;
    margin-bottom: 1.5rem;
    padding-top: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #111827;
}}

/* Dossier-Titel (erstes h1) */
.dossier-result h1:first-of-type {{
    font-size: 1.75rem;
    font-weight: 300;
    letter-spacing: 0.025em;
    text-transform: none;
    margin-top: 0;
    padding-top: 0;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e5e7eb;
}}

/* h2 = Unterüberschriften: Eisbrecher, Themen-Cluster, etc. */
.dossier-result h2 {{
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    padding-top: 0;
    border-top: none;
}}

/* h3 = Blöcke: BLOCK 1, BLOCK 2, etc. */
.dossier-result h3 {{
    font-size: 0.95rem;
    font-weight: 600;
    color: #4b5563;
    margin-top: 1.25rem;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}

.dossier-result blockquote {{
    background-color: #f9fafb;
    border-left: 3px solid #111827;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
    border-radius: 0 0.25rem 0.25rem 0;
    font-size: 0.875rem;
}}

.dossier-result blockquote a {{
    color: #111827;
    text-decoration: underline;
    text-underline-offset: 2px;
    font-weight: 500;
}}

.dossier-result blockquote a:hover {{
    color: #4b5563;
}}

.dossier-result ul {{
    padding-left: 1.25rem;
}}

.dossier-result li {{
    margin-bottom: 0.5rem;
    line-height: 1.75;
    color: #4b5563;
}}

.dossier-result strong {{
    font-weight: 600;
    color: #111827;
}}

.dossier-result hr {{
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 3.5rem 0;
}}

/* Sidebar items */
.sidebar-item {{
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    color: #4b5563;
    transition: background-color 0.15s ease;
    cursor: pointer;
}}

.sidebar-item:hover {{
    background-color: #f9fafb;
}}

/* Warning box for disambiguation */
.disambig-warning {{
    background-color: #fef3c7;
    border-left: 4px solid #f59e0b;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
    border-radius: 0 0.5rem 0.5rem 0;
    font-size: 0.875rem;
    color: #92400e;
}}

/* Action buttons */
.stButton > button {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 500;
    border-radius: 0.5rem;
    transition: all 0.15s ease;
}}

/* Primary button: grün wenn aktiv, grau wenn disabled */
.stButton > button[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {{
    background-color: #16a34a !important;
    color: #ffffff !important;
    border: none !important;
}}

.stButton > button[data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {{
    background-color: #15803d !important;
}}

.stButton > button[data-testid="baseButton-primary"]:disabled,
.stButton > button[kind="primary"]:disabled {{
    background-color: #d1d5db !important;
    color: #9ca3af !important;
    cursor: not-allowed !important;
    opacity: 1 !important;
}}

.stButton > button[data-testid="baseButton-secondary"] {{
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #e5e7eb;
}}

.stButton > button[data-testid="baseButton-secondary"]:hover {{
    background-color: #f9fafb;
    border-color: #9ca3af;
}}

/* Status messages */
div[data-testid="stAlert"] {{
    border-radius: 0.5rem;
    font-size: 0.875rem;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid #e5e7eb;
}}

.stTabs [data-baseweb="tab"] {{
    font-family: 'Inter', sans-serif;
    font-size: 0.875rem;
    font-weight: 500;
    color: #4b5563;
    padding: 0.75rem 1.25rem;
}}

.stTabs [aria-selected="true"] {{
    color: #111827;
    border-bottom-color: #111827;
}}

/* Expander */
.streamlit-expanderHeader {{
    font-family: 'Inter', sans-serif;
    font-size: 0.875rem;
    font-weight: 500;
    color: #4b5563;
}}

/* Text input */
.stTextInput input {{
    font-family: 'Inter', sans-serif;
    border-radius: 0.5rem;
    border: 1px solid #e5e7eb !important;
    padding: 0.625rem 0.75rem;
    font-size: 0.875rem;
}}

.stTextInput input:focus {{
    border-color: #9ca3af !important;
    box-shadow: none !important;
}}

/* Override Streamlit red/colored focus ring */
.stTextInput div[data-baseweb="input"] {{
    border-color: #e5e7eb !important;
    background-color: #ffffff !important;
}}

.stTextInput div[data-baseweb="input"]:focus-within {{
    border-color: #9ca3af !important;
    box-shadow: none !important;
}}

/* Hide "Press Enter to Apply" tooltip */
.stTextInput div[data-testid="InputInstructions"] {{
    display: none !important;
}}

/* Also target via attribute in newer Streamlit versions */
.stTextInput [data-testid="stWidgetLabel"] + div div[class*="instructions"],
.stTextInput .st-emotion-cache-1gulkj5 {{
    display: none !important;
}}

/* Download button */
.stDownloadButton > button {{
    font-family: 'Inter', sans-serif;
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    font-weight: 500;
}}

.stDownloadButton > button:hover {{
    background-color: #f9fafb;
    border-color: #9ca3af;
}}

</style>
""", unsafe_allow_html=True)


# --- Passwort-Schutz ---
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

if APP_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("""
        <div class="app-header">
            <h1 class="app-title">DAS! Gästedossier</h1>
            <p class="app-subtitle">Zugang nur für autorisierte Nutzer</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            col_pw, col_login, col_space = st.columns([2, 1, 3])
            with col_pw:
                password = st.text_input("Passwort eingeben", type="password", key="login_pw")
            with col_login:
                st.markdown('<div style="height: 1.65rem;"></div>', unsafe_allow_html=True)
                login = st.form_submit_button("Anmelden", use_container_width=True)

        if login:
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Falsches Passwort.")
        st.stop()


# --- Header ---
st.markdown("""
<div class="app-header">
    <h1 class="app-title">DAS! Gästedossier</h1>
    <p class="app-subtitle">Automatisierte Moderations-Dossiers für DAS! Rote Sofa (NDR)</p>
</div>
""", unsafe_allow_html=True)

# --- Session State ---
if "step" not in st.session_state:
    st.session_state.step = "input"
if "session_dossiers" not in st.session_state:
    st.session_state.session_dossiers = {}  # {guest: {"content": str, "filename": str}}
if "session_research" not in st.session_state:
    st.session_state.session_research = {}  # {guest: {"content": str, "filename": str}}

# --- Sidebar ---
with st.sidebar:
    st.markdown("## Bisherige Dossiers")
    dossier_dir = PROJECT_ROOT / "dossiers"
    shown_dossiers = False

    # Datei-basiert (lokal/persistent)
    if dossier_dir.exists():
        file_dossiers = sorted(dossier_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        for d in file_dossiers:
            if st.button(f"📄 {d.stem}", key=f"sidebar_{d.name}", use_container_width=True):
                st.session_state["view_dossier"] = d
            shown_dossiers = True

    # Session-basiert (Cloud-kompatibel)
    for g, data in st.session_state.session_dossiers.items():
        key = f"sess_d_{data['filename']}"
        label = data["filename"].replace(".md", "")
        if st.button(f"📄 {label}", key=key, use_container_width=True):
            st.session_state["view_dossier_content"] = data["content"]
        shown_dossiers = True

    if not shown_dossiers:
        st.caption("Noch keine Dossiers erstellt.")

    st.divider()
    st.markdown("## Research-Daten")
    tmp_dir = PROJECT_ROOT / ".tmp"
    shown_research = False

    # Datei-basiert (lokal/persistent)
    if tmp_dir.exists():
        research_files = sorted(
            [f for f in tmp_dir.glob("*_research.md") if "_raw" not in f.name],
            key=lambda f: f.stat().st_mtime, reverse=True,
        )
        for r in research_files:
            if st.button(f"🔍 {r.stem}", key=f"sidebar_r_{r.name}", use_container_width=True):
                st.session_state["view_research"] = r
            shown_research = True

    # Session-basiert (Cloud-kompatibel)
    for g, data in st.session_state.session_research.items():
        key = f"sess_r_{data['filename']}"
        label = data["filename"].replace("_research.md", "").replace("_", " ")
        if st.button(f"🔍 {label}", key=key, use_container_width=True):
            st.session_state["view_research_content"] = data["content"]
        shown_research = True

    if not shown_research:
        st.caption("Noch keine Research-Daten.")

# --- Sidebar views ---
if "view_dossier" in st.session_state:
    dossier_path = st.session_state.pop("view_dossier")
    st.markdown(f'<div class="dossier-result">{dossier_path.read_text(encoding="utf-8")}</div>', unsafe_allow_html=True)
    st.stop()

if "view_dossier_content" in st.session_state:
    content = st.session_state.pop("view_dossier_content")
    st.markdown(f'<div class="dossier-result">{content}</div>', unsafe_allow_html=True)
    st.stop()

if "view_research" in st.session_state:
    research_path = st.session_state.pop("view_research")
    raw_path = research_path.parent / research_path.name.replace("_research.md", "_research_raw.md")
    if raw_path.exists():
        tab_verified, tab_raw = st.tabs(["✅ Verifiziert", "📦 Rohdaten (API-Original)"])
        with tab_verified:
            st.markdown(f'<div class="research-data-view">{research_path.read_text(encoding="utf-8")}</div>', unsafe_allow_html=True)
        with tab_raw:
            st.markdown(f'<div class="research-data-view">{raw_path.read_text(encoding="utf-8")}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="research-data-view">{research_path.read_text(encoding="utf-8")}</div>', unsafe_allow_html=True)
    st.stop()

if "view_research_content" in st.session_state:
    content = st.session_state.pop("view_research_content")
    st.markdown(f'<div class="research-data-view">{content}</div>', unsafe_allow_html=True)
    st.stop()


# ============================================================
# SCHRITT 1: Name eingeben
# ============================================================
if st.session_state.step == "input":
    col_input, col_btn, col_spacer = st.columns([2, 1, 3])
    with col_input:
        guest_name = st.text_input(
            "Gastname",
            placeholder="z.B. Udo Lindenberg",
            key="guest_input",
            label_visibility="visible",
        )
    with col_btn:
        st.markdown('<div style="height: 1.65rem;"></div>', unsafe_allow_html=True)
        check_button = st.button("Person prüfen", type="primary", use_container_width=True)

    if check_button and not guest_name:
        st.warning("Bitte einen Gastnamen eingeben.")
    elif check_button and guest_name:
        with st.spinner("Identität wird geprüft..."):
            try:
                candidates, is_ambiguous = disambiguate_guest(guest_name)
                st.session_state.candidates = candidates
                st.session_state.is_ambiguous = is_ambiguous
                st.session_state.guest_input_name = guest_name

                if is_ambiguous:
                    st.session_state.step = "disambiguate"
                else:
                    selected = candidates[0]
                    st.session_state.selected_guest = selected["name"]
                    st.session_state.context_hint = selected.get("context_hint", "")
                    st.session_state.step = "confirm"
                st.rerun()
            except Exception as e:
                st.error(f"Fehler bei der Identitätsprüfung: {e}")


# ============================================================
# SCHRITT 2a: Disambiguierung
# ============================================================
elif st.session_state.step == "disambiguate":
    st.markdown(f"""
    <div class="disambig-warning">
        <strong>Mehrere Personen gefunden</strong> für den Namen „{st.session_state.guest_input_name}". Bitte wähle die richtige Person aus.
    </div>
    """, unsafe_allow_html=True)

    for i, c in enumerate(st.session_state.candidates):
        st.markdown(f"""
        <div class="disambig-card">
            <h4>{c['name']}</h4>
            <p>{c['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Auswählen: {c['name']}", key=f"select_{i}", use_container_width=True):
            st.session_state.selected_guest = c["name"]
            st.session_state.context_hint = c.get("context_hint", "")
            st.session_state.step = "confirm"
            st.rerun()

    st.divider()
    if st.button("↩ Zurück", use_container_width=False):
        st.session_state.step = "input"
        st.rerun()


# ============================================================
# SCHRITT 2b: Bestätigung
# ============================================================
elif st.session_state.step == "confirm":
    guest = st.session_state.selected_guest
    hint = st.session_state.context_hint

    st.markdown(f"""
    <div class="identity-card">
        <h3>{guest}</h3>
        <p>{hint if hint else 'Eindeutig identifiziert'}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Dossier erstellen", type="primary", use_container_width=True):
            st.session_state.step = "running"
            st.rerun()
    with col2:
        if st.button("Andere Person", use_container_width=True):
            st.session_state.step = "input"
            st.rerun()


# ============================================================
# SCHRITT 3: Pipeline läuft
# ============================================================
elif st.session_state.step == "running":
    guest = st.session_state.selected_guest
    hint = st.session_state.get("context_hint", "")

    st.markdown(f"""
    <div class="identity-card">
        <h3>{guest}</h3>
        <p>{hint if hint else ''}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Schritt 1: Research ---
    step1_status = st.empty()
    step1_status.markdown("""
    <div class="pipeline-step">
        <div class="pipeline-step-header">
            <div class="step-number active">1</div>
            <span class="step-title">Deep Research</span>
        </div>
        <div class="active-progress"></div>
    </div>
    """, unsafe_allow_html=True)

    research_status = st.empty()
    research_status.caption("Perplexity Deep Research + Tavily Echtzeit-Check + Verifikation...")

    try:
        research_path = run_research(guest, context_hint=hint)

        # Research in session_state sichern (Cloud-kompatibel)
        st.session_state.session_research[guest] = {
            "content": research_path.read_text(encoding="utf-8"),
            "filename": research_path.name,
        }

        # Step 1 als erledigt markieren (ersetzt den aktiven Balken komplett)
        step1_status.markdown("""
        <div class="pipeline-step">
            <div class="pipeline-step-header">
                <div class="step-number done">✓</div>
                <span class="step-title">Deep Research — abgeschlossen</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        research_status.empty()

        with st.expander("Research-Daten anzeigen", expanded=False):
            raw_path = research_path.parent / research_path.name.replace("_research.md", "_research_raw.md")
            if raw_path.exists():
                tab_verified, tab_raw = st.tabs(["✅ Verifiziert", "📦 Rohdaten"])
                with tab_verified:
                    st.markdown(f'<div class="research-data-view">{research_path.read_text(encoding="utf-8")}</div>', unsafe_allow_html=True)
                with tab_raw:
                    st.markdown(f'<div class="research-data-view">{raw_path.read_text(encoding="utf-8")}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="research-data-view">{research_path.read_text(encoding="utf-8")}</div>', unsafe_allow_html=True)
    except Exception as e:
        research_status.empty()
        st.error(f"Research fehlgeschlagen: {e}")
        if st.button("↩ Zurück"):
            st.session_state.step = "input"
            st.rerun()
        st.stop()

    # --- Schritt 2: Dossier ---
    step2_status = st.empty()
    step2_status.markdown("""
    <div class="pipeline-step">
        <div class="pipeline-step-header">
            <div class="step-number active">2</div>
            <span class="step-title">Dossier wird erstellt</span>
        </div>
        <div class="active-progress"></div>
    </div>
    """, unsafe_allow_html=True)

    dossier_live = st.empty()
    dossier_live.caption("Claude schreibt das Dossier...")

    try:
        # Streaming: Live-Vorschau des Dossiers (mit dossier-result Wrapper für korrektes CSS)
        def update_preview(content_so_far):
            dossier_live.markdown(f'<div class="dossier-result">{content_so_far}</div>', unsafe_allow_html=True)

        dossier_path = create_dossier(guest, research_path, on_chunk=update_preview)

        # Step 2 als erledigt (ersetzt den aktiven Balken komplett)
        step2_status.markdown("""
        <div class="pipeline-step">
            <div class="pipeline-step-header">
                <div class="step-number done">✓</div>
                <span class="step-title">Dossier — abgeschlossen</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        dossier_live.empty()

    except Exception as e:
        dossier_live.empty()
        st.error(f"Dossier-Erstellung fehlgeschlagen: {e}")
        if st.button("↩ Zurück"):
            st.session_state.step = "input"
            st.rerun()
        st.stop()

    # --- Ergebnis ---
    dossier_content = dossier_path.read_text(encoding="utf-8")

    # Dossier in session_state sichern (Cloud-kompatibel)
    st.session_state.session_dossiers[guest] = {
        "content": dossier_content,
        "filename": dossier_path.name,
    }

    st.markdown(f'<div class="dossier-result">{dossier_content}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.download_button(
            label="Dossier herunterladen",
            data=dossier_content,
            file_name=dossier_path.name,
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        research_data = st.session_state.session_research.get(guest, {})
        if research_data:
            st.download_button(
                label="Research herunterladen",
                data=research_data["content"],
                file_name=research_data["filename"],
                mime="text/markdown",
                use_container_width=True,
            )
    with col3:
        if st.button("Neues Dossier", use_container_width=True):
            st.session_state.step = "input"
            st.rerun()

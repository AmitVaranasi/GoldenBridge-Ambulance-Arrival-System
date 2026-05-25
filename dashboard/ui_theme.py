"""
Golden Bridge — clinical dashboard UI theme (Streamlit HTML/CSS helpers).
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional

# Severity → presentation tokens
SEVERITY_STYLES: Dict[str, Dict[str, str]] = {
    "CRITICAL": {"bg": "#FEF2F2", "border": "#DC2626", "text": "#991B1B", "accent": "#DC2626", "label": "Critical"},
    "EMERGENT": {"bg": "#FFF7ED", "border": "#EA580C", "text": "#9A3412", "accent": "#EA580C", "label": "Emergent"},
    "URGENT": {"bg": "#FFFBEB", "border": "#D97706", "text": "#92400E", "accent": "#D97706", "label": "Urgent"},
    "NON-EMERGENT": {"bg": "#ECFDF5", "border": "#059669", "text": "#065F46", "accent": "#059669", "label": "Non-emergent"},
    "UNKNOWN": {"bg": "#F1F5F9", "border": "#94A3B8", "text": "#475569", "accent": "#64748B", "label": "Assessing"},
}

ALERT_STYLES: Dict[str, Dict[str, str]] = {
    "STEMI": {"icon": "♥", "title": "STEMI", "sub": "Activate Cath Lab", "color": "#DC2626"},
    "STROKE": {"icon": "◉", "title": "Stroke", "sub": "Stroke team + CT", "color": "#7C3AED"},
    "TRAUMA": {"icon": "✦", "title": "Trauma", "sub": "Trauma bay activation", "color": "#EA580C"},
    "SEPSIS": {"icon": "◎", "title": "Sepsis", "sub": "Sepsis bundle", "color": "#0D9488"},
    "CARDIAC_ARREST_RISK": {"icon": "!", "title": "Arrest risk", "sub": "Code blue prep", "color": "#B91C1C"},
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FFFFFF",
    font=dict(family="DM Sans, sans-serif", size=12, color="#334155"),
    margin=dict(l=48, r=24, t=40, b=36),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

PLOTLY_AXIS = dict(
    gridcolor="#E2E8F0",
    linecolor="#CBD5E1",
    tickfont=dict(size=11, color="#64748B"),
)


def inject_global_css() -> str:
    return """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
    :root {
        --gb-primary: #0E7490;
        --gb-primary-dark: #155E75;
        --gb-bg: #E8EEF4;
        --gb-card: #FFFFFF;
        --gb-text: #0F172A;
        --gb-muted: #64748B;
        --gb-border: #E2E8F0;
        --gb-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.06);
        --gb-radius: 14px;
        --gb-font: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        --gb-mono: 'IBM Plex Mono', ui-monospace, monospace;
    }

    .stApp {
        background: linear-gradient(165deg, #E8EEF4 0%, #F8FAFC 42%, #E2E8F0 100%);
        font-family: var(--gb-font);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F2942 0%, #163A5C 55%, #1E4D6B 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #F8FAFC !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.12);
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        color: #F1F5F9 !important;
        border-radius: 10px !important;
        font-family: var(--gb-font) !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.12) !important;
        border-color: rgba(255,255,255,0.25) !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0E7490, #0891B2) !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(14, 116, 144, 0.45);
    }

    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    h1, h2, h3, h4, p, label {
        font-family: var(--gb-font) !important;
    }

    /* Main panel — dark text on light background (fixes invisible metrics/vitals) */
    section[data-testid="stMain"] {
        color: #0F172A;
    }
    section[data-testid="stMain"] [data-testid="stMetricLabel"],
    section[data-testid="stMain"] [data-testid="stMetricLabel"] p {
        color: #64748B !important;
        font-family: var(--gb-font) !important;
    }
    section[data-testid="stMain"] [data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-family: var(--gb-mono) !important;
        font-weight: 600 !important;
        font-size: 1.75rem !important;
    }
    section[data-testid="stMain"] [data-testid="stMetricDelta"] {
        color: #475569 !important;
    }
    section[data-testid="stMain"] [data-testid="stMetricDelta"] svg {
        fill: #475569 !important;
    }
    section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4,
    section[data-testid="stMain"] h5,
    section[data-testid="stMain"] h6,
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] li,
    section[data-testid="stMain"] strong {
        color: #0F172A !important;
    }
    section[data-testid="stMain"] [data-testid="stCaptionContainer"],
    section[data-testid="stMain"] .stCaption {
        color: #64748B !important;
    }
    section[data-testid="stMain"] [data-testid="stTabs"] button {
        color: #475569 !important;
    }
    section[data-testid="stMain"] [data-testid="stTabs"] button[aria-selected="true"] {
        color: #0E7490 !important;
        border-bottom-color: #0E7490 !important;
    }
    section[data-testid="stMain"] [data-testid="stExpander"] summary {
        color: #0F172A !important;
        background-color: #F1F5F9 !important;
        border-radius: 8px;
    }
    section[data-testid="stMain"] [data-testid="stExpander"] details {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
    }
    section[data-testid="stMain"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stMain"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
        color: #334155 !important;
    }
    section[data-testid="stMain"] [data-testid="stAlert"] p,
    section[data-testid="stMain"] [data-testid="stAlert"] div {
        color: #1E293B !important;
    }
    section[data-testid="stMain"] [data-testid="stNotificationContent"] {
        color: #1E293B !important;
    }
    section[data-testid="stMain"] [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #E2E8F0 !important;
    }

    .gb-section-title {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--gb-muted);
        margin: 1.5rem 0 0.75rem 0;
    }

    .gb-brand-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
        background: var(--gb-card);
        border: 1px solid var(--gb-border);
        border-radius: var(--gb-radius);
        padding: 1.1rem 1.5rem;
        box-shadow: var(--gb-shadow);
        margin-bottom: 1.25rem;
    }
    .gb-brand-bar .logo-mark {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background: linear-gradient(135deg, #0E7490, #155E75);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .gb-brand-bar h1 {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--gb-text);
        margin: 0;
        letter-spacing: -0.03em;
    }
    .gb-brand-bar .tagline {
        font-size: 0.85rem;
        color: var(--gb-muted);
        margin: 0.15rem 0 0 0;
    }
    .gb-pill-row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
    .gb-pill {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        border: 1px solid var(--gb-border);
        background: #F8FAFC;
        color: var(--gb-muted);
    }
    .gb-pill.live {
        background: #ECFDF5;
        border-color: #A7F3D0;
        color: #047857;
    }
    .gb-pill.live::before {
        content: '';
        display: inline-block;
        width: 6px;
        height: 6px;
        background: #10B981;
        border-radius: 50%;
        margin-right: 6px;
        animation: gb-pulse 1.5s ease infinite;
    }
    @keyframes gb-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.85); }
    }
    .gb-pill.hipaa {
        background: #EFF6FF;
        border-color: #BFDBFE;
        color: #1D4ED8;
    }

    .gb-patient-hero {
        background: var(--gb-card);
        border-radius: var(--gb-radius);
        border: 1px solid var(--gb-border);
        box-shadow: var(--gb-shadow);
        overflow: hidden;
        margin-bottom: 1rem;
    }
    .gb-patient-hero .hero-top {
        padding: 1.35rem 1.5rem;
        border-left: 5px solid var(--hero-accent, #0E7490);
        background: linear-gradient(90deg, #FFFFFF 0%, #F8FAFC 100%);
    }
    .gb-patient-hero .pid {
        font-family: var(--gb-mono);
        font-size: 0.8rem;
        color: var(--gb-muted);
        margin-bottom: 0.35rem;
    }
    .gb-patient-hero h2 {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--gb-text);
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .gb-patient-hero .meta {
        display: flex;
        flex-wrap: wrap;
        gap: 1.25rem;
        font-size: 0.9rem;
        color: var(--gb-muted);
    }
    .gb-patient-hero .meta strong { color: var(--gb-text); }

    .gb-stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 0.75rem;
    }
    .gb-stat-card {
        background: var(--gb-card);
        border: 1px solid var(--gb-border);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04);
    }
    .gb-stat-card .label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--gb-muted);
        margin-bottom: 0.35rem;
    }
    .gb-stat-card .value {
        font-family: var(--gb-mono);
        font-size: 1.35rem;
        font-weight: 500;
        color: var(--gb-text);
        line-height: 1.2;
    }
    .gb-stat-card .delta {
        font-size: 0.75rem;
        color: var(--delta-color, var(--gb-muted));
        margin-top: 0.35rem;
        font-weight: 500;
    }

    .gb-alert-banner {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        padding: 0.9rem 1.1rem;
        border-radius: 12px;
        border: 1px solid;
        margin-bottom: 0.65rem;
        animation: gb-alert-in 0.4s ease;
    }
    @keyframes gb-alert-in {
        from { opacity: 0; transform: translateY(-6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .gb-alert-banner .icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.1rem;
        color: white;
        flex-shrink: 0;
    }
    .gb-alert-banner.critical-pulse {
        animation: gb-alert-in 0.4s ease, gb-glow 2s ease-in-out infinite;
    }
    @keyframes gb-glow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        50% { box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.15); }
    }

    .gb-score-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
    }
    @media (max-width: 1100px) {
        .gb-score-grid { grid-template-columns: repeat(2, 1fr); }
    }

    .gb-panel {
        background: var(--gb-card);
        border: 1px solid var(--gb-border);
        border-radius: var(--gb-radius);
        padding: 1.25rem 1.35rem;
        box-shadow: var(--gb-shadow);
        height: 100%;
    }
    .gb-panel h3 {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--gb-text);
        margin: 0 0 1rem 0;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid var(--gb-border);
    }

    .gb-resource-row {
        margin-bottom: 0.85rem;
    }
    .gb-resource-row .row-head {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        margin-bottom: 0.35rem;
        color: #CBD5E1;
    }
    .gb-resource-row .bar {
        height: 6px;
        background: rgba(255,255,255,0.12);
        border-radius: 999px;
        overflow: hidden;
    }
    .gb-resource-row .fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s ease;
    }

    .gb-fleet-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
    }
    .gb-fleet-card.selected {
        border-color: #22D3EE;
        background: rgba(14, 116, 144, 0.25);
    }
    .gb-severity-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }

    .gb-handoff {
        background: linear-gradient(135deg, #F0FDFA 0%, #ECFEFF 100%);
        border: 1px solid #99F6E4;
        border-radius: var(--gb-radius);
        padding: 1.25rem 1.5rem;
        color: #134E4A;
        line-height: 1.65;
        font-size: 0.92rem;
    }
    .gb-handoff strong { color: #0F766E; }

    .gb-treatment-item {
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--gb-border);
    }
    .gb-treatment-item:last-child { border-bottom: none; }
    .gb-treatment-item .name {
        font-weight: 600;
        color: var(--gb-text);
        font-size: 0.9rem;
    }
    .gb-treatment-item .detail {
        font-size: 0.8rem;
        color: var(--gb-muted);
        margin-top: 0.2rem;
    }

    .gb-voice-feed {
        max-height: 220px;
        overflow-y: auto;
    }
    .gb-voice-note {
        background: #F8FAFC;
        border-left: 3px solid #0E7490;
        padding: 0.75rem 1rem;
        margin-bottom: 0.65rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.85rem;
        color: #334155;
        line-height: 1.5;
    }
    .gb-voice-note .time {
        font-family: var(--gb-mono);
        font-size: 0.7rem;
        color: var(--gb-muted);
        margin-bottom: 0.35rem;
    }

    .gb-protocol {
        margin-bottom: 0.75rem;
        padding: 1rem;
        background: #F8FAFC;
        border-radius: 10px;
        border: 1px solid var(--gb-border);
    }
    .gb-protocol .name {
        font-weight: 700;
        font-size: 0.85rem;
        color: var(--gb-primary-dark);
        margin-bottom: 0.5rem;
    }
    .gb-protocol li {
        font-size: 0.82rem;
        color: #475569;
        margin-bottom: 0.25rem;
    }

    .gb-pred-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #F0F9FF;
        border: 1px solid #BAE6FD;
        color: #0369A1;
        padding: 0.5rem 0.85rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.25rem 0.35rem 0.25rem 0;
    }
    .gb-pred-chip .conf {
        font-family: var(--gb-mono);
        font-size: 0.72rem;
        opacity: 0.85;
    }

    .gb-eta-ring {
        text-align: center;
        padding: 1rem;
    }
    .gb-eta-ring .ring-value {
        font-family: var(--gb-mono);
        font-size: 2.5rem;
        font-weight: 500;
        color: var(--gb-primary-dark);
        line-height: 1;
    }
    .gb-eta-ring .ring-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--gb-muted);
        margin-top: 0.35rem;
    }

    .gb-sidebar-stat {
        display: flex;
        justify-content: space-between;
        background: rgba(255,255,255,0.06);
        padding: 0.6rem 0.85rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }
</style>
"""


def _esc(text: Any) -> str:
    return html.escape(str(text)) if text is not None else ""


def brand_header(
    ambulance_count: int,
    en_route: int,
    clock: str,
) -> str:
    return f"""
    <div class="gb-brand-bar">
        <div style="display:flex;align-items:center;gap:1rem;">
            <div class="logo-mark">GB</div>
            <div>
                <h1>Golden Bridge</h1>
                <p class="tagline">Pre-Arrival Clinical Command · Real-time EMS → ED handoff</p>
            </div>
        </div>
        <div class="gb-pill-row">
            <span class="gb-pill live">Live telemetry</span>
            <span class="gb-pill hipaa">HIPAA · Aparavi redaction</span>
            <span class="gb-pill">{_esc(ambulance_count)} active transports</span>
            <span class="gb-pill">{_esc(en_route)} en route</span>
            <span class="gb-pill" style="font-family:var(--gb-mono);">{_esc(clock)}</span>
        </div>
    </div>
    """


def patient_hero(
    patient_id: str,
    ambulance_id: str,
    age: int,
    gender: str,
    complaint: str,
    status: str,
    eta: int,
    severity_level: str,
) -> str:
    style = SEVERITY_STYLES.get(severity_level, SEVERITY_STYLES["UNKNOWN"])
    if status == "ARRIVED":
        status_html = '<span style="color:#059669;font-weight:600;">● Arrived — handoff ready</span>'
    else:
        status_html = f'<span style="color:#0E7490;font-weight:600;">● En route · ETA {_esc(eta)} min</span>'

    return f"""
    <div class="gb-patient-hero">
        <div class="hero-top" style="--hero-accent:{style['accent']};">
            <div class="pid">{_esc(patient_id)} · {_esc(ambulance_id)}</div>
            <h2>{_esc(complaint)}</h2>
            <div class="meta">
                <span><strong>{_esc(age)}</strong> years · {_esc(gender)}</span>
                <span>{status_html}</span>
                <span style="padding:0.2rem 0.65rem;border-radius:6px;background:{style['bg']};
                    color:{style['text']};border:1px solid {style['border']};font-weight:600;font-size:0.8rem;">
                    {style['label']}
                </span>
            </div>
        </div>
    </div>
    """


def eta_severity_panel(eta: int, status: str, severity: Dict[str, Any]) -> str:
    level = severity.get("level", "UNKNOWN")
    score = severity.get("score", 0)
    style = SEVERITY_STYLES.get(level, SEVERITY_STYLES["UNKNOWN"])

    if status == "ARRIVED":
        eta_block = """
        <div class="gb-eta-ring">
            <div class="ring-value" style="color:#059669;">✓</div>
            <div class="ring-label">Patient arrived</div>
        </div>
        """
    else:
        eta_block = f"""
        <div class="gb-eta-ring">
            <div class="ring-value">{_esc(eta)}</div>
            <div class="ring-label">Minutes to ED</div>
        </div>
        """

    return f"""
    <div class="gb-panel">
        {eta_block}
        <div style="text-align:center;padding-top:0.75rem;border-top:1px solid var(--gb-border);">
            <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--gb-muted);">
                AI severity index
            </div>
            <div style="font-family:var(--gb-mono);font-size:2rem;font-weight:500;color:{style['accent']};">
                {_esc(score)}<span style="font-size:1rem;color:var(--gb-muted);">/100</span>
            </div>
            <div style="font-weight:600;color:{style['text']};font-size:0.9rem;">{style['label']}</div>
        </div>
    </div>
    """


def vital_stat_cards(vitals: Dict[str, Any]) -> str:
    if not vitals:
        return '<p style="color:var(--gb-muted);">Awaiting telemetry…</p>'

    hr = vitals.get("heart_rate", "—")
    spo2 = vitals.get("spo2", "—")
    bp = vitals.get("blood_pressure", "—")

    def hr_color(v):
        if isinstance(v, int) and (v > 120 or v < 50):
            return "#DC2626"
        return "var(--gb-text)"

    def spo2_color(v):
        if isinstance(v, int) and v < 92:
            return "#DC2626"
        if isinstance(v, int) and v < 94:
            return "#D97706"
        return "var(--gb-text)"

    cards = [
        ("Heart rate", f"{hr}", "bpm", hr_color(hr)),
        ("SpO₂", f"{spo2}", "%", spo2_color(spo2)),
        ("Blood pressure", bp, "", "var(--gb-text)"),
    ]
    inner = ""
    for label, val, unit, color in cards:
        unit_s = f' <span style="font-size:0.85rem;color:var(--gb-muted);">{unit}</span>' if unit else ""
        inner += f"""
        <div class="gb-stat-card">
            <div class="label">{label}</div>
            <div class="value" style="color:{color};">{_esc(val)}{unit_s}</div>
        </div>
        """
    return f'<div class="gb-stat-grid">{inner}</div>'


def score_cards_grid(patient_data: Dict[str, Any]) -> str:
    scores = patient_data.get("clinical_scores", {})
    severity = patient_data.get("severity", {})
    if not scores:
        return ""

    items = [
        ("Severity", f"{severity.get('score', 0)}/100", severity.get("level", "")),
        ("Shock index", str(scores["shock_index"]["value"]), scores["shock_index"]["interpretation"]),
        ("STEMI", str(scores["stemi_checklist"]["score"]), scores["stemi_checklist"]["interpretation"]),
        ("qSOFA", f"{scores['qsofa']['score']}/3", scores["qsofa"]["interpretation"]),
        ("Trauma (RTS)", str(scores["trauma_score"]["score"]), scores["trauma_score"]["interpretation"]),
        ("NIHSS", f"{scores['nihss']['score']}/42", scores["nihss"]["interpretation"]),
        ("Airway risk", str(scores["airway_risk"]["score"]), scores["airway_risk"]["interpretation"]),
        ("Deterioration", str(scores["deterioration"]["score"]), scores["deterioration"]["interpretation"]),
    ]

    cells = ""
    for label, value, delta in items:
        level = severity.get("level", "")
        delta_color = SEVERITY_STYLES.get(level, SEVERITY_STYLES["UNKNOWN"])["accent"] if label == "Severity" else "var(--gb-muted)"
        cells += f"""
        <div class="gb-stat-card">
            <div class="label">{_esc(label)}</div>
            <div class="value">{_esc(value)}</div>
            <div class="delta" style="--delta-color:{delta_color};">{_esc(delta)}</div>
        </div>
        """
    return f'<div class="gb-score-grid">{cells}</div>'


def alert_banners(alerts: List[str]) -> str:
    if not alerts:
        return ""
    html_parts = ['<div class="gb-section-title" style="margin-top:0;">Active clinical alerts</div>']
    for alert in alerts:
        meta = ALERT_STYLES.get(alert, {"icon": "!", "title": alert, "sub": "", "color": "#64748B"})
        pulse = " critical-pulse" if alert in ("STEMI", "CARDIAC_ARREST_RISK") else ""
        html_parts.append(f"""
        <div class="gb-alert-banner{pulse}" style="background:#FEF2F2;border-color:{meta['color']};">
            <div class="icon" style="background:{meta['color']};">{meta['icon']}</div>
            <div>
                <div style="font-weight:700;color:#0F172A;font-size:0.95rem;">{meta['title']}</div>
                <div style="font-size:0.8rem;color:#64748B;">{meta['sub']}</div>
            </div>
        </div>
        """)
    return "".join(html_parts)


def predictions_html(predictions: Dict[str, Any], confidence: Dict[str, float]) -> str:
    chips = []
    labels = {
        "cardiac_arrest_imminent": "Cardiac arrest risk",
        "needs_intubation": "Intubation likely",
        "needs_icu": "ICU admission",
        "needs_or": "OR required",
        "likely_stroke": "Stroke pathway",
        "likely_stemi": "STEMI pathway",
        "likely_sepsis": "Sepsis pathway",
    }
    conf_keys = {
        "cardiac_arrest_imminent": "cardiac_arrest",
        "needs_intubation": "intubation",
        "needs_icu": "icu",
        "needs_or": "or",
        "likely_stroke": "stroke",
        "likely_stemi": "stemi",
        "likely_sepsis": "sepsis",
    }
    for key, label in labels.items():
        if predictions.get(key):
            ck = conf_keys.get(key, key)
            pct = int(confidence.get(ck, 0.75) * 100)
            chips.append(
                f'<span class="gb-pred-chip">{_esc(label)}'
                f'<span class="conf">{pct}%</span></span>'
            )
    if not chips:
        return '<p style="color:var(--gb-muted);font-size:0.85rem;">No high-confidence interventions predicted.</p>'
    return "".join(chips)


def protocols_html(protocols: Dict[str, List[str]]) -> str:
    if not protocols:
        return '<p style="color:var(--gb-muted);font-size:0.85rem;">No protocols activated.</p>'
    parts = []
    for name, actions in protocols.items():
        title = name.replace("_", " ").title()
        lis = "".join(f"<li>{_esc(a)}</li>" for a in actions)
        parts.append(f'<div class="gb-protocol"><div class="name">{_esc(title)}</div><ul style="margin:0;padding-left:1.1rem;">{lis}</ul></div>')
    return "".join(parts)


def handoff_html(summary: str) -> str:
    import re

    parts = re.split(r"(\*\*.+?\*\*)", summary, flags=re.DOTALL)
    chunks = []
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            chunks.append(f"<strong>{_esc(part[2:-2])}</strong>")
        else:
            chunks.append(_esc(part))
    body = "".join(chunks).replace("\n\n", "<br><br>").replace("\n", "<br>")
    return f'<div class="gb-handoff">{body}</div>'


def resource_bar(label: str, available: int, total: Optional[int] = None) -> str:
    if total and total > 0:
        pct = int((available / total) * 100)
        count = f"{available}/{total}"
        if pct > 50:
            fill = "#34D399"
        elif pct > 20:
            fill = "#FBBF24"
        else:
            fill = "#F87171"
    else:
        pct = 100 if available > 0 else 0
        count = str(available)
        fill = "#34D399" if available > 0 else "#F87171"

    return f"""
    <div class="gb-resource-row">
        <div class="row-head"><span>{_esc(label)}</span><span>{_esc(count)}</span></div>
        <div class="bar"><div class="fill" style="width:{pct}%;background:{fill};"></div></div>
    </div>
    """


def sidebar_fleet_hint(patient_id: str, amb_id: str, eta: int, level: str, status: str, selected: bool) -> str:
    style = SEVERITY_STYLES.get(level, SEVERITY_STYLES["UNKNOWN"])
    sel = " selected" if selected else ""
    if status == "ARRIVED":
        status_txt = "Arrived"
    else:
        status_txt = f"ETA {eta} min"
    return f"""
    <div class="gb-fleet-card{sel}">
        <span class="gb-severity-dot" style="background:{style['accent']};"></span>
        <strong>{_esc(patient_id)}</strong> · {_esc(amb_id)}<br>
        <span style="opacity:0.75;">{status_txt} · {style['label']}</span>
    </div>
    """


def apply_plotly_theme(fig) -> None:
    """Apply chart styling; must not raise (Streamlit would print the error)."""
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(**PLOTLY_AXIS)
    fig.update_yaxes(**PLOTLY_AXIS)


def show_html(fragment: str) -> None:
    """Render HTML reliably on Streamlit 1.27+ (prefer over markdown for fragments)."""
    import streamlit as st

    st.html(fragment)

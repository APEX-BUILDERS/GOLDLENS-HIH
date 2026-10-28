"""Presentation-only styles for the GoldLens Streamlit dashboard."""

from __future__ import annotations

import streamlit as st


PLOTLY_LAYOUT = {
    "template": "plotly_white",
    "font": {"family": "Inter, Segoe UI, system-ui, sans-serif", "color": "#111827"},
    "paper_bgcolor": "#ffffff",
    "plot_bgcolor": "#ffffff",
    "colorway": ["#0B1050", "#117A8B", "#D4A63A", "#475569"],
    "margin": {"l": 18, "r": 18, "t": 56, "b": 24},
    "xaxis": {"gridcolor": "#E5E7EB", "zerolinecolor": "#E5E7EB"},
    "yaxis": {"gridcolor": "#E5E7EB", "zerolinecolor": "#E5E7EB"},
}


def apply_theme() -> None:
    """Apply CSS only; all data and behavior remains in the dashboard module."""
    st.markdown(
        """
        <style>
        .stApp { background: #F4F5F9; color: #111827; font-family: Inter, "Segoe UI", system-ui, sans-serif; }
        #MainMenu, footer, header { visibility: hidden; }
        .block-container { max-width: 1280px; padding-top: 0; padding-bottom: 0; }
        .utility-bar { background:#0B1050; color:#fff; font-size:.78rem; padding:.55rem max(1rem, calc((100vw - 1248px)/2)); margin:0 calc(50% - 50vw); display:flex; justify-content:space-between; gap:1rem; }
        .brand-header { background:#fff; margin:0 calc(50% - 50vw); padding:1.15rem max(1rem, calc((100vw - 1248px)/2)); display:flex; align-items:center; justify-content:space-between; gap:1.5rem; box-shadow:0 1px 6px rgba(11,16,80,.08); }
        .wordmark { display:flex; align-items:center; gap:.65rem; color:#0B1050; font-size:1.55rem; font-weight:800; letter-spacing:-.04em; }
        .header-logo { display:block; width:220px; height:auto; max-width:100%; }
        .fallback-wordmark { color:#0B1050; font-size:1.55rem; font-weight:850; letter-spacing:-.04em; }
        .fallback-wordmark span { color:#D4A63A; }
        .tagline { color:#64748B; font-size:.82rem; margin-top:.15rem; }
        .info-strip { display:flex; gap:1.4rem; flex-wrap:wrap; }
        .info-label { color:#64748B; font-size:.66rem; text-transform:uppercase; letter-spacing:.08em; font-weight:700; }
        .info-value { color:#0B1050; font-size:.84rem; font-weight:750; }
        .status-negative { color:#A73636; } .status-positive { color:#08715C; }
        .hero { margin:1.35rem 0 1rem; padding:2.35rem; border-radius:18px; color:#fff; background:radial-gradient(circle at 20% 10%, rgba(212,166,58,.24), transparent 30%), linear-gradient(120deg,#060B2A,#0B1050); display:flex; min-height:220px; align-items:center; gap:1rem; overflow:hidden; }
        .hero-copy { flex:1.25; } .hero-wordmark { color:#fff; font-size:.84rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; margin-bottom:.65rem; } .hero h1 { margin:0 0 .55rem; font-size:clamp(2rem,4vw,3.2rem); line-height:1.05; letter-spacing:-.05em; color:white; }
        .hero p { color:#C7D2FE; font-size:1rem; max-width:650px; margin:0 0 1.25rem; }
        .chips { display:flex; flex-wrap:wrap; gap:.45rem; } .chip { border:1px solid rgba(212,166,58,.8); color:#fff; border-radius:999px; padding:.35rem .65rem; font-size:.78rem; font-weight:700; } .chip span { color:#F5D67B; font-weight:600; }
        .hero-art { flex:.75; max-width:320px; min-width:190px; }
        .section-card { background:#fff; border-radius:16px; box-shadow:0 5px 20px rgba(15,23,42,.07); padding:1.25rem 1.35rem; margin:.8rem 0 1.3rem; }
        .section-title { color:#0B1050; font-size:1.28rem; font-weight:800; letter-spacing:-.02em; margin:0 0 .25rem; }
        .section-note { color:#64748B; font-size:.86rem; margin:0 0 1rem; }
        .kpi-card, .step-card, .spec-card { background:#fff; border-radius:15px; box-shadow:0 5px 18px rgba(15,23,42,.07); padding:1.1rem; min-height:104px; border-top:3px solid #D4A63A; }
        .kpi-label, .step-number { color:#64748B; font-size:.7rem; text-transform:uppercase; letter-spacing:.07em; font-weight:750; } .kpi-value { color:#0B1050; font-size:1.45rem; font-weight:850; margin:.4rem 0; } .kpi-detail, .step-copy { color:#475569; font-size:.83rem; }
        .step-title { color:#0B1050; font-weight:800; margin:.3rem 0; }
        .spec-card { border-top-color:#117A8B; min-height:0; } .spec-card h3 { margin:0 0 .5rem; color:#0B1050; } .spec-card p { margin:.18rem 0; color:#475569; font-size:.83rem; }
        .unverified { color:#A73636; font-weight:750; }
        .footer { margin:1.6rem calc(50% - 50vw) 0; padding:1.4rem max(1rem, calc((100vw - 1248px)/2)); background:#0B1050; color:#DCE3F9; font-size:.78rem; line-height:1.5; } .footer strong { color:#F5D67B; }
        .stTabs [data-baseweb="tab-list"] { gap:0; background:linear-gradient(90deg,#0A2A5A,#117A8B); border-radius:10px; padding:0 .35rem; } .stTabs [data-baseweb="tab"] { height:46px; color:#fff; font-weight:750; } .stTabs [aria-selected="true"] { background:rgba(255,255,255,.09); } .stTabs [data-baseweb="tab-highlight"] { background-color:#D4A63A; height:3px; }
        @media(max-width: 760px) { .utility-bar, .brand-header, .hero { flex-direction:column; align-items:flex-start; } .info-strip { gap:.75rem; } .hero { padding:1.5rem; } .hero-art { display:none; } }
        </style>
        """,
        unsafe_allow_html=True,
    )

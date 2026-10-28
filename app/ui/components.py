"""Small presentation components used by the dashboard."""

from __future__ import annotations

from html import escape

import streamlit as st


def card(title: str, note: str = "") -> None:
    st.markdown(f'<div class="section-card"><div class="section-title">{escape(title)}</div><p class="section-note">{escape(note)}</p>', unsafe_allow_html=True)


def close_card() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def kpi(label: str, value: str, detail: str = "") -> None:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">{escape(label)}</div><div class="kpi-value">{escape(value)}</div><div class="kpi-detail">{escape(detail)}</div></div>', unsafe_allow_html=True)


def step(number: int, title: str, copy: str) -> None:
    st.markdown(f'<div class="step-card"><div class="step-number">0{number}</div><div class="step-title">{escape(title)}</div><div class="step-copy">{escape(copy)}</div></div>', unsafe_allow_html=True)


def spec(symbol: str, values: dict[str, object]) -> None:
    rule = str(values["listing_rule"]).replace("TODO(verify)", '<span class="unverified">unverified</span>')
    st.markdown(
        f'<div class="spec-card"><h3>{escape(symbol)}</h3><p>{values["lot_unit_grams"]}g lot · {values["quote_base_grams"]}g quote base · {values["purity"]} purity</p><p>Expiry window: {escape(str(values["expiry_window"]))}</p><p>Listing rule: {rule}</p></div>',
        unsafe_allow_html=True,
    )

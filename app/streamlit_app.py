"""Streamlit entry point for the GoldLens dashboard."""

import streamlit as st


st.set_page_config(page_title="GoldLens", page_icon="🟨", layout="wide")
st.title("GoldLens")
st.caption("MCX gold futures normalization and spread analysis")
st.info("Setup complete. Add real MCX Bhavcopy CSV files to data/raw/ to begin ingestion.")

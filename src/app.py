import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
from utils import *

# Page config
st.set_page_config(page_title="Derivatives Analyzer", layout="wide")

# --- Top disclaimer (always visible) ---
st.warning("Disclaimer: This is educational content only and not investment advice. Do your own research before trading.", icon="⚠️")

# App title
st.title("F&O Participant Analysis")

# Divider
st.divider()

# Date selectors
col1, col2 = st.columns(2)

with col1:
    current_date = st.date_input(
        "Current Date",
        value=current_working_day(date.today())
    )

with col2:
    prev_date = st.date_input(
        "Previous Date",
        value=previous_working_day(current_date)
    )

st.divider()

# Compute button
col1, col2 = st.columns(2)
with col1:
    compute_btn = st.button("🚀 Start Computing", type="primary")
with col2:
    clear_cache_btn = st.button("🗑️ Clear Cache")

if clear_cache_btn:
    scrape_nsedata.clear()
    st.success("Cache cleared successfully!")

if compute_btn:
# Validation
    if prev_date >= current_date:
        st.error("⚠️ Previous Date must be earlier than Current Date.")
    elif current_date > date.today():
        st.error("⚠️ Current Date cannot be in the future.")
    else:
        st.success(f"✅ Selected period: **{prev_date}** to **{current_date}**")

        # Optional loader to simulate computation
        with st.status("Processing F&O Participant data...", expanded=True) as status:
            status.update(label="📥 Fetching data from source & 🧹 Cleaning it...")
            part_df, fii_curr_df, fii_prev_df = scrape_nsedata(filepath= Path(__file__).parents[1] / "data", prevDate= prev_date, currentDate= current_date)

            status.update(label="📊 Running participant analysis...")
            signals, part_oi, curr_fii_oi, prev_fii_oi = compute_ratios(part_df, fii_curr_df, fii_prev_df)

            status.update(
                label="F&O Participant Analysis is ready!",
                state="complete",
                expanded=False,
            )
    
            # Display results
            st.subheader(f"**{current_date}** OI Data")
            st.dataframe(part_df)

            st.subheader(f"**{current_date}** FII's OI Data")
            st.dataframe(fii_curr_df)

            st.subheader(f"**{prev_date}** FII's OI Data")
            st.dataframe(fii_prev_df)

            st.divider()
            
            # Display analysis per instrument
            st.header("Instrument-wise Analysis")
            for instrument in signals:
                category = 'INDEX FUTURES' if 'FUTURES' in instrument and 'STOCK' not in instrument else 'STOCK FUTURES' if instrument == 'STOCK FUTURES' else 'INDEX OPTIONS' if 'OPTIONS' in instrument and 'STOCK' not in instrument else 'STOCK OPTIONS' if instrument == 'STOCK OPTIONS' else None
                if category:
                    st.subheader(f"{instrument}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"Participant OI ({category})", f"{part_oi[category]:,.0f}")
                    with col2:
                        st.metric("Current FII OI", f"{curr_fii_oi[instrument]:,.0f}")
                    with col3:
                        st.metric("Previous FII OI", f"{prev_fii_oi.get(instrument, 0):,.0f}")
                    
                    if "LONG" in signals[instrument]:
                        st.success(signals[instrument])
                    elif "SHORT" in signals[instrument]:
                        st.success(signals[instrument])
                    else:
                        st.info(signals[instrument])
                    st.divider()
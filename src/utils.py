import streamlit as st
import requests
from io import StringIO, BytesIO
import pandas as pd
import numpy as np
from datetime import date, timedelta

@st.cache_data(ttl=21600) # Caching for 6 hours...
def scrape_nsedata(filepath, prevDate, currentDate):
    BASE = "https://nsearchives.nseindia.com/content"
    urls = {
        "participant": f"{BASE}/nsccl/fao_participant_oi_{currentDate:%d%m%Y}.csv",
        "fii_curr": f"{BASE}/fo/fii_stats_{currentDate:%d-%b-%Y}.xls",
        "fii_prev": f"{BASE}/fo/fii_stats_{prevDate:%d-%b-%Y}.xls",
    }
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.nseindia.com",
        "Connection": "keep-alive",
    })
    session.get("https://www.nseindia.com", timeout=10)

    # Participant OI
    part_df = fetch_csv(session, urls["participant"], skiprows=1)
    part_df.columns = part_df.columns.str.strip().str.replace(" ", "_")

    # part_df.to_csv(
    #     filepath / f"Deriv_Part_Curr_DF_{currentDate:%d%m%Y}.csv",
    #     index=False
    # )

    # FII Stats
    fii_curr_df = convert_numeric(fetch_nse_excel(session, urls["fii_curr"]))
    fii_prev_df = convert_numeric(fetch_nse_excel(session, urls["fii_prev"]))

    # fii_curr.to_csv(
    #     filepath / f"Deriv_FII_Curr_DF_{currentDate:%d%m%Y}.csv",
    #     index=False
    # )
    # fii_prev.to_csv(
    #     filepath / f"Deriv_FII_Prev_DF_{prevDate:%d%m%Y}.csv",
    #     index=False
    # )
    return part_df, fii_curr_df, fii_prev_df


def current_working_day(d: date | None = None) -> date:
    if d is None:
        d = date.today()

    while d.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        d -= timedelta(days=1)

    return d


def previous_working_day(d: date) -> date:
    d -= timedelta(days=1)
    while d.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        d -= timedelta(days=1)
    return d


def fetch_csv(session, url, skiprows=0):
    r = session.get(url)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text), skiprows=skiprows)


def fetch_nse_excel(session, url):
    r = session.get(url)
    r.raise_for_status()

    df = pd.read_excel(BytesIO(r.content), skiprows=1, header=[0, 1])

    cols = []
    for col in df.columns:
        if col[0].startswith("Unnamed"):
            cols.append("Instrument")
        else:
            cols.append(
                f"{col[0]}_{col[1]}"
                .strip()
                .replace(" ", "_")
                .replace(".", "")
            )

    df.columns = cols

    df = (
        df.replace(r"^\s*$", np.nan, regex=True)
          .dropna(how="any")
          .reset_index(drop=True)
    )

    return df


def convert_numeric(df:pd.DataFrame, exclude=("Instrument",)):
    num_cols = df.columns.difference(exclude)

    df[num_cols] = (
        df[num_cols]
        .astype(str)
        .replace({",": ""}, regex=True)
        .apply(pd.to_numeric, errors="coerce")
    )

    df = df.dropna(subset=num_cols).reset_index(drop=True)
    return df


def compute_ratios(part_df: pd.DataFrame, fii_curr_df: pd.DataFrame, fii_prev_df: pd.DataFrame):
    # Exclude TOTAL row
    part_df = part_df[part_df['Client_Type'] != 'TOTAL']

    # Calculate participant OI per category
    participant_oi = {
        'INDEX FUTURES': (part_df['Future_Index_Long'] - part_df['Future_Index_Short']).sum(),
        'STOCK FUTURES': (part_df['Future_Stock_Long'] - part_df['Future_Stock_Short']).sum(),
        'INDEX OPTIONS': ((part_df['Option_Index_Call_Long'] + part_df['Option_Index_Put_Long']) - (part_df['Option_Index_Call_Short'] + part_df['Option_Index_Put_Short'])).sum(),
        'STOCK OPTIONS': ((part_df['Option_Stock_Call_Long'] + part_df['Option_Stock_Put_Long']) - (part_df['Option_Stock_Call_Short'] + part_df['Option_Stock_Put_Short'])).sum(),
    }
    # compare forml: today oi > prev day oi + FIIs positive >>> long
    # Get FII OI per instrument
    print(fii_curr_df)
    curr_fii_oi = fii_curr_df.set_index('Instrument')['OPEN_INTEREST_AT_THE_END_OF_THE_DAY_No_of_contracts'].to_dict()
    prev_fii_oi = fii_prev_df.set_index('Instrument')['OPEN_INTEREST_AT_THE_END_OF_THE_DAY_No_of_contracts'].to_dict()
    curr_sell_amt = fii_curr_df.set_index('Instrument')['SELL_Amt_in_Crores'].to_dict()
    curr_buy_amt = fii_curr_df.set_index('Instrument')['BUY_Amt_in_Crores'].to_dict()
    
    # Function to get category for instrument
    def get_category(instrument):
        if 'FUTURES' in instrument and 'STOCK' not in instrument:
            return 'INDEX FUTURES'
        elif instrument == 'STOCK FUTURES':
            return 'STOCK FUTURES'
        elif 'OPTIONS' in instrument and 'STOCK' not in instrument:
            return 'INDEX OPTIONS'
        elif instrument == 'STOCK OPTIONS':
            return 'STOCK OPTIONS'
        else:
            return None
    
    # Generate signals per instrument
    signals = {}
    for instrument in curr_fii_oi:
        category = get_category(instrument)
        if category:
            curr_oi = participant_oi[category]
            curr_fii = curr_fii_oi[instrument]
            prev_fii = prev_fii_oi.get(instrument, 0)  # default 0 if not present
            sell_amt = curr_sell_amt.get(instrument, 0)
            buy_amt = curr_buy_amt.get(instrument, 0)
            net_sell = sell_amt - buy_amt
            if net_sell > 0 and curr_oi > prev_fii:
                signals[instrument] = f"Possible LONG: Net sell ({net_sell:.2f}) > 0 and Participant OI ({curr_oi}) > Prev FII OI ({prev_fii})"
            elif net_sell < 0 and curr_oi < prev_fii:
                signals[instrument] = f"Possible SHORT: Net buy ({net_sell:.2f}) < 0 and Participant OI ({curr_oi}) < Prev FII OI ({prev_fii})"
            else:
                signals[instrument] = "No clear trading signal based on the current derivatives OI data."
    
    return signals, participant_oi, curr_fii_oi, prev_fii_oi
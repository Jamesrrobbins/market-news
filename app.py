import streamlit as st
import news_engine as engine
import json
import os

st.set_page_config(page_title="Market Prime", page_icon="📉", layout="wide")

# CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetric"] { background-color: #1c1f26; border: 1px solid #2d303e; padding: 10px; border-radius: 8px; }
    div[data-testid="stForm"] { border: none; padding: 0;}
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# WATCHLIST LOGIC
WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f: return json.load(f)
        except: pass
    return ["AAPL", "NVDA", "TSLA"] 

def save_watchlist(new_list):
    with open(WATCHLIST_FILE, "w") as f: json.dump(new_list, f)

if 'stock_list' not in st.session_state:
    st.session_state['stock_list'] = load_watchlist()

# --- SETTINGS ---
with st.expander("⚙️ Settings", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        loc = st.text_input("Location", value="Auchterarder")
    with c2:
        with st.form("add_stock", clear_on_submit=True):
            new_ticker = st.text_input("Add Ticker")
            if st.form_submit_button("Add") and new_ticker:
                t = new_ticker.upper().strip()
                if t not in st.session_state['stock_list']:
                    st.session_state['stock_list'].append(t)
                    save_watchlist(st.session_state['stock_list'])
                    st.rerun()

    if st.button("Clear Watchlist"):
        st.session_state['stock_list'] = []
        save_watchlist([])
        st.rerun()

st.title("📉 Market Prime")

# --- SECTION 1: LOCAL & WEATHER ---
col1, col2 = st.columns([1, 2])
with col1:
    w = engine.get_weather(loc)
    if w and "error" not in w:
        st.metric(f"{loc[:10]}", w['temp'], w['condition'])
        st.caption(f"Wind: {w['wind']}")
    else:
        st.error("Weather N/A")

with col2:
    with st.spinner(f"Searching Google News for {loc}..."):
        # USE GOOGLE NEWS HERE
        news = engine.get_google_news(query=f"{loc} Scotland news", limit=5)
        if news:
            st.info(engine.generate_summary(news, loc))
            with st.expander(f"Read {loc} News"):
                for n in news:
                    st.write(f"• [{n['title']}]({n['url']}) - *{n['source']}*")
        else:
            st.warning("No local news found.")

st.divider()

# --- SECTION 2: GLOBAL & UK ---
c_glob, c_uk = st.columns(2)
with c_glob:
    st.subheader("🌍 Global Biz")
    # Use Google for broad market news
    n_glob = engine.get_google_news(query="Stock Market News Global", limit=5)
    st.success(engine.generate_summary(n_glob, "Global Markets"))

with c_uk:
    st.subheader("🇬🇧 UK Headlines")
    # Use Google for UK specifically
    n_uk = engine.get_google_news(query="UK News Headlines", limit=5)
    st.success(engine.generate_summary(n_uk, "UK National"))

st.divider()

# --- SECTION 3: WATCHLIST ---
st.subheader("Active Watchlist")

if not st.session_state['stock_list']:
    st.info("Watchlist empty. Add stocks in Settings.")

for ticker in st.session_state['stock_list']:
    data = engine.get_stock_data(ticker)
    
    with st.container():
        # TITLE & PRICE
        c_head, c_del = st.columns([4, 1])
        c_head.markdown(f"### {ticker} <span style='font-size:0.8em; color:#aaa'>({data['price']})</span>", unsafe_allow_html=True)
        if c_del.button("✕", key=f"del_{ticker}"):
            st.session_state['stock_list'].remove(ticker)
            save_watchlist(st.session_state['stock_list'])
            st.rerun()
        
        # 3 METRICS
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"**24H:** :{data['color_1d']}[{data['chg_1d']}]")
        m2.markdown(f"**1M:** :{data['color_1m']}[{data['chg_1m']}]")
        m3.markdown(f"**1Y:** :{data['color_1y']}[{data['chg_1y']}]")
        
        # ANALYSIS
        st.write("")
        if data['news']:
            st.info(engine.generate_summary(data['news'], f"{ticker}"))
            with st.expander(f"Sources: {ticker}"):
                for n in data['news']:
                    st.write(f"• [{n['title']}]({n['url']})")
        else:
            st.caption("No recent news found.")
        
        st.markdown("---")
        

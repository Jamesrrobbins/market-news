import streamlit as st
import news_engine as engine
import json
import os

# PAGE SETUP
st.set_page_config(page_title="Market Prime", page_icon="📉", layout="wide")

# CSS STYLING
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        border: 1px solid #2d303e;
        padding: 15px;
        border-radius: 8px;
    }
    .stAlert {
        background-color: #151922;
        border: 1px solid #363b47;
        color: #e0e0e0;
    }
    div[data-testid="stForm"] { border: none; padding: 0;}
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# PERSISTENCE (Save/Load Watchlist)
WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return ["AAPL", "NVDA", "TSLA"] 

def save_watchlist(new_list):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(new_list, f)

if 'stock_list' not in st.session_state:
    st.session_state['stock_list'] = load_watchlist()

def remove_stock_action(ticker_to_remove):
    if ticker_to_remove in st.session_state['stock_list']:
        st.session_state['stock_list'].remove(ticker_to_remove)
        save_watchlist(st.session_state['stock_list'])

# --- APP LAYOUT ---

with st.expander("⚙️ Settings & Watchlist Manager", expanded=False):
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📍 Location")
        user_location = st.text_input("Local News Area", value="Auchterarder, Scotland")
    with c2:
        st.subheader("➕ Add Stock")
        with st.form("add_stock_form", clear_on_submit=True):
            new_ticker = st.text_input("Enter Ticker (e.g. AMZN)")
            submitted = st.form_submit_button("Add Stock", use_container_width=True)
            if submitted and new_ticker:
                ticker_clean = new_ticker.upper().strip()
                if ticker_clean not in st.session_state['stock_list']:
                    st.session_state['stock_list'].append(ticker_clean)
                    save_watchlist(st.session_state['stock_list'])
                    st.rerun()

    st.caption(f"Watching: {', '.join(st.session_state['stock_list'])}")
    if st.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        st.rerun()

st.title("📉 Market Prime")

# SECTION A: LOCAL INTELLIGENCE
col_w, col_news = st.columns([1, 2])
with col_w:
    weather = engine.get_weather(user_location)
    if weather and "error" not in weather:
        st.caption(f"Weather Source: {weather['source']}")
        c1, c2 = st.columns(2)
        c1.metric("Temp", weather['temp'], weather['condition'])
        c2.metric("Wind", weather['wind'], weather['humidity'])
    else:
        st.error(f"Weather unavailable for {user_location}")

with col_news:
    with st.spinner(f"Scanning intel for {user_location}..."):
        local_news = engine.get_news(query=user_location, limit=5)
        if local_news:
            summary = engine.generate_summary(local_news, f"Local ({user_location})")
            st.info(f"**📍 {user_location} Intel**\n\n{summary}")
        else:
            st.warning(f"No specific news found for {user_location} today.")

st.divider()

# SECTION B: GLOBAL INTELLIGENCE
g_col, uk_col = st.columns(2)
with g_col:
    st.subheader("🌍 Global Headlines")
    global_news = engine.get_news(category='business', limit=7)
    g_sum = engine.generate_summary(global_news, "Global Market")
    st.success(g_sum)
    with st.expander("Show Sources"):
        for n in global_news[:5]:
            st.markdown(f"• [{n['title']}]({n['url']})")

with uk_col:
    st.subheader("🇬🇧 UK Briefing")
    uk_news = engine.get_news(domains='bbc.co.uk,theguardian.com,news.sky.com', limit=7)
    uk_sum = engine.generate_summary(uk_news, "UK National")
    st.success(uk_sum)
    with st.expander("Show Sources"):
        for n in uk_news[:5]:
            st.markdown(f"• [{n['title']}]({n['url']})")

st.divider()

# SECTION C: WATCHLIST
st.subheader("📈 Active Watchlist")

if not st.session_state['stock_list']:
    st.info("Your watchlist is empty. Open 'Settings' at the top to add stocks.")

for ticker in st.session_state['stock_list']:
    with st.spinner(f"Loading {ticker}..."):
        data = engine.get_stock_data(ticker)
    
    if data and "error" not in data:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 0.5])
            c1.markdown(f"### {ticker} <span style='color:gray; font-size:0.8em'>${data['price']:.2f}</span>", unsafe_allow_html=True)
            c2.metric("1D", f"{data['chg_1d']:.2f}%")
            c3.metric("1M", f"{data['chg_1mo']:.2f}%")
            c4.metric("1Y", f"{data['chg_1y']:.2f}%")
            
            # Delete Button
            if c5.button("✕", key=f"del_{ticker}"):
                remove_stock_action(ticker)
                st.rerun()
            
            if data['news']:
                ai_col, link_col = st.columns([3, 1])
                with ai_col:
                    s_sum = engine.generate_summary(data['news'], f"{ticker} Stock")
                    st.info(s_sum)
                with link_col:
                    st.caption("Read More:")
                    for n in data['news'][:3]:
                        st.markdown(f"[[Link]]({n['url']}) {n['title'][:15]}...")
            st.markdown("---")
            
    else:
        # VISUAL ERROR CARD
        with st.container():
            st.error(f"⚠️ Could not load data for **{ticker}**. It may be delisted or the API is blocking requests.")
            if st.button("Delete", key=f"del_err_{ticker}"):
                remove_stock_action(ticker)
                st.rerun()
                

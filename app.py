import streamlit as st
import news_engine as engine

# PAGE SETUP
st.set_page_config(page_title="Market Prime", page_icon="📉", layout="wide")

# 1. CUSTOM CSS (The "Look Better" Part)
st.markdown("""
<style>
    /* Darker Backgrounds for Cards */
    .stApp { background-color: #0e1117; }
    
    /* Style the Metrics (Stock Prices/Weather) */
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        border: 1px solid #2d303e;
        padding: 15px;
        border-radius: 8px;
    }
    
    /* Style the AI Summary Box */
    .stAlert {
        background-color: #151922;
        border: 1px solid #363b47;
        color: #e0e0e0;
    }
    
    /* Remove padding from top */
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# 2. SESSION STATE (The "Add Stocks" Part)
if 'stock_list' not in st.session_state:
    st.session_state['stock_list'] = ["AAPL", "NVDA", "TSLA"] # Default start list

def add_stock():
    new_stock = st.session_state.new_stock_input.upper().strip()
    if new_stock and new_stock not in st.session_state['stock_list']:
        st.session_state['stock_list'].append(new_stock)

def remove_stock(ticker):
    st.session_state['stock_list'].remove(ticker)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Location
    user_location = st.text_input("📍 Location", "London")
    
    st.divider()
    
    # Stock Manager
    st.subheader("Manage Watchlist")
    st.text_input("Add Ticker (e.g. MSFT)", key="new_stock_input", on_change=add_stock)
    
    st.write("Current List:")
    for stock in st.session_state['stock_list']:
        c1, c2 = st.columns([3, 1])
        c1.write(f"• {stock}")
        if c2.button("✕", key=f"remove_{stock}"):
            remove_stock(stock)
            st.rerun()

    st.divider()
    if st.button("🔄 Full Refresh", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- MAIN PAGE ---
st.title("📉 Market Prime")

# SECTION A: LOCATION & WEATHER
col_w, col_news = st.columns([1, 2])

with col_w:
    weather = engine.get_weather(user_location)
    if weather and "error" not in weather:
        st.caption(f"Weather: {weather['source']}")
        c1, c2 = st.columns(2)
        c1.metric("Temp", weather['temp'], weather['condition'])
        c2.metric("Wind", weather['wind'], weather['humidity'])
    else:
        st.error("Weather unavailable")

with col_news:
    with st.spinner("Analyzing local intel..."):
        # Fetch 7 items for better context
        local_news = engine.get_news(query=user_location, limit=7)
        if local_news:
            summary = engine.generate_summary(local_news, f"Local ({user_location})")
            st.info(f"**📍 {user_location} Intel**\n\n{summary}")
            
            # Clickable Links Expander
            with st.expander("📖 Read Full Local Stories"):
                for n in local_news:
                    st.markdown(f"• [{n['title']}]({n['url']}) - *{n['source']}*")
        else:
            st.warning("No local news found.")

st.divider()

# SECTION B: GLOBAL INTELLIGENCE
g_col, uk_col = st.columns(2)

with g_col:
    st.subheader("🌍 Global Headlines")
    global_news = engine.get_news(category='business', limit=10)
    g_sum = engine.generate_summary(global_news, "Global Market")
    st.success(g_sum)
    
    with st.expander("🔗 Top Global Stories"):
        for n in global_news[:5]:
            st.markdown(f"• [{n['title']}]({n['url']})")

with uk_col:
    st.subheader("🇬🇧 UK Briefing")
    # Priority Domains
    uk_news = engine.get_news(domains='bbc.co.uk,theguardian.com,news.sky.com', limit=10)
    uk_sum = engine.generate_summary(uk_news, "UK National")
    st.success(uk_sum)
    
    with st.expander("🔗 Top UK Stories"):
        for n in uk_news[:5]:
            st.markdown(f"• [{n['title']}]({n['url']})")

st.divider()

# SECTION C: LIVE PORTFOLIO
st.subheader("📈 Active Watchlist")

# Loop through Session State list
for ticker in st.session_state['stock_list']:
    data = engine.get_stock_data(ticker)
    
    if data:
        with st.container():
            # Header Row
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(f"### {ticker} <span style='color:gray; font-size:0.8em'>${data['price']:.2f}</span>", unsafe_allow_html=True)
            c2.metric("1D", f"{data['chg_1d']:.2f}%")
            c3.metric("1M", f"{data['chg_1mo']:.2f}%")
            c4.metric("1Y", f"{data['chg_1y']:.2f}%")
            
            # AI Insight + Links
            if data['news']:
                ai_col, link_col = st.columns([3, 1])
                with ai_col:
                    s_sum = engine.generate_summary(data['news'], f"{ticker} Stock")
                    st.info(s_sum)
                with link_col:
                    st.caption("Key Sources:")
                    for n in data['news'][:3]:
                        st.markdown(f"[[Read]]({n['url']}) {n['title'][:20]}...")
            
            st.markdown("---")
            

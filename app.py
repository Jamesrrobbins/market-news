import streamlit as st
import news_engine as engine

# PAGE SETUP
st.set_page_config(page_title="News Dashboard", page_icon="📰", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .css-1r6slb0 { background-color: #262730; border-radius: 10px; padding: 20px; }
    .stAlert { background-color: #1E1E1E; border: 1px solid #333; color: #EEE; }
</style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.title("⚙️ Settings")
    user_location = st.text_input("📍 Location", "Stratford-upon-Avon")
    user_stocks = st.text_input("📈 Stocks", "MELI, CRWD, AAPL")
    stock_list = [s.strip().upper() for s in user_stocks.split(',')]
    
    if st.button("Refresh All"):
        st.cache_data.clear()
        st.rerun()

st.title("📰 News Dashboard")

# 1. LOCATION & WEATHER (Met Office)
st.subheader(f"📍 Local Updates: {user_location}")
col1, col2 = st.columns([1, 2])

with col1:
    weather = engine.get_weather(user_location)
    if weather and "error" not in weather:
        st.caption(f"Source: {weather['source']}")
        c1, c2 = st.columns(2)
        c1.metric("Temperature", weather['temp'], f"Feels {weather['feels_like']}")
        c2.metric("Condition", weather['condition'])
        
        c3, c4 = st.columns(2)
        c3.metric("Wind", weather['wind'])
        c4.metric("Humidity", weather['humidity'])
    else:
        st.error("Could not load weather.")

with col2:
    with st.spinner("Scanning local sources..."):
        local_news = engine.get_news(query=user_location, limit=5)
        if local_news:
            summary = engine.generate_summary("\n".join(local_news), "Local")
            st.info(f"✨ **AI Summary:**\n\n{summary}")
        else:
            st.warning("No specific local news found today.")

st.divider()

# 2. GLOBAL & NATIONAL (Trusted Sources)
c_global, c_national = st.columns(2)

with c_global:
    st.subheader("🌍 Global News")
    global_news = engine.get_news(category='general', limit=5)
    g_sum = engine.generate_summary("\n".join(global_news), "Global")
    st.info(g_sum)

with c_national:
    st.subheader("🇬🇧 UK News (BBC / Guardian / Sky)")
    # Forces these 3 specific domains
    uk_news = engine.get_news(domains='bbc.co.uk,theguardian.com,news.sky.com', limit=5)
    uk_sum = engine.generate_summary("\n".join(uk_news), "National UK")
    st.info(uk_sum)

st.divider()

# 3. STOCK WATCHLIST
st.subheader("📈 Stock Watchlist")

for ticker in stock_list:
    data = engine.get_stock_data(ticker)
    
    if data:
        with st.expander(f"**{ticker}** (${data['price']:.2f})", expanded=True):
            m1, m2, m3 = st.columns(3)
            m1.metric("1 Day", f"{data['chg_1d']:.2f}%", f"{data['chg_1d']:.2f}%")
            m2.metric("1 Month", f"{data['chg_1mo']:.2f}%", f"{data['chg_1mo']:.2f}%")
            m3.metric("1 Year", f"{data['chg_1y']:.2f}%", f"{data['chg_1y']:.2f}%")
            
            if data['news']:
                st.write("---")
                s_sum = engine.generate_summary("\n".join(data['news']), f"{ticker} Stock")
                st.success(f"✨ **AI Insight:** {s_sum}")
            else:
                st.caption("No recent news headlines.")
                

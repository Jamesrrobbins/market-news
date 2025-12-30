import streamlit as st
import news_engine as engine

# PAGE SETUP
st.set_page_config(page_title="News Dashboard", page_icon="📰", layout="wide")

# CUSTOM CSS (To mimic the Dark Card UI)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .css-1r6slb0 { background-color: #262730; border-radius: 10px; padding: 20px; }
    /* Style for the "AI Summary" Box */
    .stAlert { background-color: #1E1E1E; border: 1px solid #333; color: #EEE; }
</style>
""", unsafe_allow_html=True)

# SIDEBAR: CONTROLS
with st.sidebar:
    st.title("⚙️ Settings")
    user_location = st.text_input("📍 Location", "Auchterarder, Scotland")
    user_stocks = st.text_input("📈 Stocks (comma separated)", "MELI, CRWD, AAPL")
    stock_list = [s.strip().upper() for s in user_stocks.split(',')]
    
    if st.button("Refresh All"):
        st.cache_data.clear()
        st.rerun()

st.title("📰 News Dashboard")
st.caption("Stay informed with AI-powered news summaries")

# 1. LOCATION & WEATHER SECTION
st.subheader(f"📍 Local Updates: {user_location}")
col1, col2 = st.columns([1, 2])

with col1:
    # WEATHER CARDS
    weather = engine.get_weather(user_location)
    if weather and "error" not in weather:
        c1, c2 = st.columns(2)
        c1.metric("Temperature", weather['temp'], f"Feels {weather['feels_like']}")
        c2.metric("Condition", weather['condition'])
        
        c3, c4 = st.columns(2)
        c3.metric("Wind", weather['wind'])
        c4.metric("Humidity", weather['humidity'])
    else:
        st.error("Could not load weather.")

with col2:
    # LOCAL NEWS CARD
    with st.spinner("Scanning local sources..."):
        local_news = engine.get_news(query=user_location, limit=5)
        if local_news:
            summary = engine.generate_summary("\n".join(local_news), "Local")
            st.info(f"✨ **AI Summary:**\n\n{summary}")
            with st.expander("Read Sources"):
                for story in local_news:
                    st.write(f"• {story}")
        else:
            st.warning("No specific local news found today.")

st.divider()

# 2. GLOBAL & NATIONAL NEWS
c_global, c_national = st.columns(2)

with c_global:
    st.subheader("🌍 Global News")
    global_news = engine.get_news(category='general', limit=5)
    g_sum = engine.generate_summary("\n".join(global_news), "Global")
    st.info(g_sum)

with c_national:
    st.subheader("🇬🇧 UK News")
    uk_news = engine.get_news(country='gb', limit=5)
    uk_sum = engine.generate_summary("\n".join(uk_news), "National UK")
    st.info(uk_sum)

st.divider()

# 3. STOCK WATCHLIST
st.subheader("📈 Stock Watchlist")

for ticker in stock_list:
    data = engine.get_stock_data(ticker)
    
    if data:
        # Create a "Card" for each stock using an Expander
        with st.expander(f"**{ticker}** (${data['price']:.2f})", expanded=True):
            # The 3 Metrics (1D, 1M, 1Y)
            m1, m2, m3 = st.columns(3)
            m1.metric("1 Day", f"{data['chg_1d']:.2f}%", f"{data['chg_1d']:.2f}%")
            m2.metric("1 Month", f"{data['chg_1mo']:.2f}%", f"{data['chg_1mo']:.2f}%")
            m3.metric("1 Year", f"{data['chg_1y']:.2f}%", f"{data['chg_1y']:.2f}%")
            
            # AI Summary of stock news
            if data['news']:
                st.write("---")
                s_sum = engine.generate_summary("\n".join(data['news']), f"{ticker} Stock")
                st.success(f"✨ **AI Insight:** {s_sum}")
            else:
                st.caption("No recent news headlines.")
                with col2:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# SIDEBAR (Settings)
with st.sidebar:
    st.header("Configuration")
    
    # 1. API Keys (Input or Detect)
    if not engine.NEWS_API_KEY:
        api_key_input = st.text_input("NewsAPI Key", type="password")
        if api_key_input: engine.NEWS_API_KEY = api_key_input
        
    if not engine.OPENAI_API_KEY:
        openai_key_input = st.text_input("OpenAI Key", type="password")
        if openai_key_input: engine.OPENAI_API_KEY = openai_key_input

    st.divider()
    
    # 2. User Preferences
    st.subheader("📡 Tracking List")
    selected_stocks = st.multiselect(
        "Watchlist", 
        ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "BTC-USD", "ETH-USD"],
        ["AAPL", "NVDA", "BTC-USD"]
    )

# MAIN DASHBOARD LOGIC
if not engine.NEWS_API_KEY or not engine.OPENAI_API_KEY:
    st.warning("⚠️ Please enter your API keys in the sidebar to activate the Sphere.")
else:
    # TABS LAYOUT
    tab1, tab2, tab3 = st.tabs(["📊 Market Pulse", "🗞️ Daily Briefing", "💬 AI Analyst"])

    # TAB 1: Live Market Data (The "Dashboard" Look)
    with tab1:
        st.subheader("Live Metrics")
        
        # Create a row of cards
        cols = st.columns(len(selected_stocks))
        
        # We need a small helper to get price (mock functionality for speed, or use yfinance)
        for index, ticker in enumerate(selected_stocks):
            with cols[index]:
                # Fetch real price data
                try:
                    data = engine.yf.Ticker(ticker).history(period="1d")
                    current_price = data['Close'].iloc[-1]
                    open_price = data['Open'].iloc[-1]
                    delta = current_price - open_price
                    
                    st.metric(
                        label=ticker, 
                        value=f"${current_price:.2f}", 
                        delta=f"{delta:.2f}"
                    )
                except:
                    st.metric(label=ticker, value="Error")

    # TAB 2: The Briefing (Your original Request)
    with tab2:
        with st.spinner('Compiling your daily briefing...'):
            # Only run this expensive operation if we haven't already
            if 'summary' not in st.session_state:
                market_news = engine.get_market_news()
                stock_news = engine.get_stock_news(selected_stocks)
                st.session_state['summary'] = engine.summarize_content(market_news, stock_news)
            
            st.markdown(st.session_state['summary'])

    # TAB 3: Chat with your Data (RAG feature)
    with tab3:
        st.info("Ask questions about the news above.")
        user_query = st.text_input("Ask the Analyst:", placeholder="Why is Nvidia down today?")
        
        if user_query:
            # Simple AI interaction using the context we already have
            full_context = st.session_state.get('summary', "No news loaded yet.")
            
            prompt = f"Context:\n{full_context}\n\nUser Question: {user_query}\nAnswer:"
            
            response = engine.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            st.write(response.choices[0].message.content)


import streamlit as st
import news_engine as engine
import time

# APP CONFIGURATION
st.set_page_config(
    page_title="My Info Sphere",
    page_icon="🔮",
    layout="wide"  # This uses the full width of the screen (Dashboard style)
)

# CUSTOM CSS (To make it look like a modern app)
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 5px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# HEADER
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🔮 Info Sphere")
    st.caption("Your Personal Intelligence Dashboard")
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


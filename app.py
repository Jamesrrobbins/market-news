import streamlit as st
import news_engine as engine

st.set_page_config(page_title="Daily Market Briefing", page_icon="📈")
st.title("☕ Your Daily Market Briefing")

with st.sidebar:
    st.header("Settings")
    user_tickers = st.text_input("Enter Stocks", "AAPL, TSLA, NVDA, MSFT")
    ticker_list = [t.strip().upper() for t in user_tickers.split(',')]
    
    if st.button("Generate Digest"):
        if not engine.NEWS_API_KEY or not engine.OPENAI_API_KEY:
            st.error("⚠️ API Keys are missing! Check Streamlit Secrets.")
        else:
            with st.spinner('Reading the news...'):
                market_data = engine.get_market_news()
                stock_data = engine.get_stock_news(ticker_list)
                summary = engine.summarize_content(market_data, stock_data)
                
                st.success("Briefing Ready!")
                st.markdown("---")
                st.markdown(summary)
              

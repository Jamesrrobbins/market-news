import yfinance as yf
from newsapi import NewsApiClient
from openai import OpenAI
import streamlit as st
import os

def get_secret(key_name):
    try:
        return st.secrets[key_name]
    except (FileNotFoundError, KeyError, AttributeError):
        return os.environ.get(key_name)

NEWS_API_KEY = get_secret('NEWS_API_KEY')
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

def get_market_news():
    try:
        top_headlines = newsapi.get_top_headlines(category='business', language='en', country='us')
        articles = top_headlines.get('articles', [])[:5]
        return [f"{a['title']} - {a['source']['name']}" for a in articles]
    except Exception as e:
        return [f"Error fetching market news: {e}"]

def get_stock_news(tickers):
    stock_news = {}
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news[:3]
            headlines = [n['title'] for n in news]
            stock_news[ticker] = headlines
        except Exception as e:
            stock_news[ticker] = [f"Could not fetch news: {e}"]
    return stock_news

def summarize_content(market_news, stock_news_dict):
    market_text = "\n".join(market_news)
    stock_text = ""
    for ticker, stories in stock_news_dict.items():
        stock_text += f"\n{ticker}:\n" + "\n".join([f"- {s}" for s in stories])

    prompt = f"""
    You are a financial analyst. Summarize the following news into a daily briefing.
    
    SECTION 1: MACRO MARKET (Summarize the general vibe in 3 bullet points)
    {market_text}

    SECTION 2: MY PORTFOLIO (Give a 1-sentence takeaway for each stock based on the news)
    {stock_text}
    
    Keep it professional, concise, and actionable.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    return response.choices[0].message.content
  

import yfinance as yf
from newsapi import NewsApiClient
from openai import OpenAI
import streamlit as st
import requests
import os

# --- CONFIGURATION ---
def get_secret(key_name):
    try:
        return st.secrets[key_name]
    except:
        return os.environ.get(key_name)

NEWS_API_KEY = get_secret('NEWS_API_KEY')
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# --- WEATHER ---
def get_weather(location_name):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1&language=en&format=json"
        geo_data = requests.get(geo_url).json()
        
        if not geo_data.get('results'):
            return None
            
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&wind_speed_unit=mph&models=ukmo_seamless"
        w_data = requests.get(weather_url).json()['current']
        
        weather_codes = {0: "Clear", 1: "Mainly Clear", 2: "Cloudy", 3: "Overcast", 45: "Fog", 61: "Rain", 95: "Storm"}
        condition = weather_codes.get(w_data['weather_code'], "Variable")
        
        return {
            "temp": f"{w_data['temperature_2m']}°C",
            "wind": f"{w_data['wind_speed_10m']} mph",
            "condition": condition,
            "source": "Met Office"
        }
    except:
        return {"error": "N/A"}

# --- NEWS FETCHING ---
# FIXED: Added 'category' back to arguments
def get_news(query=None, country=None, category=None, domains=None, limit=10):
    try:
        if domains:
            data = newsapi.get_everything(q=query or 'General', domains=domains, language='en', sort_by='publishedAt')
        elif category or country:
            # logic for top headlines
            data = newsapi.get_top_headlines(country=country, category=category, language='en')
        else:
            data = newsapi.get_everything(q=query, language='en', sort_by='publishedAt')
            
        articles = data.get('articles', [])[:limit]
        return [{'title': a['title'], 'source': a['source']['name'], 'url': a['url']} for a in articles]
    except Exception as e:
        print(f"News Error: {e}")
        return []

# --- STOCK DATA (With Working Fallback) ---
def get_stock_data(ticker):
    stock_obj = {
        "symbol": ticker, 
        "price": "N/A", 
        "change": "0.00%", 
        "color": "off", 
        "news": []
    }

    # 1. Try to get Price
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if not hist.empty:
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            pct = ((curr - prev) / prev) * 100
            stock_obj["price"] = f"${curr:.2f}"
            stock_obj["change"] = f"{pct:+.2f}%"
            stock_obj["color"] = "up" if pct >= 0 else "down"
            
            if t.news:
                for n in t.news[:3]:
                    link = n.get('link') or n.get('url') or '#'
                    stock_obj["news"].append({'title': n['title'], 'url': link, 'source': 'Yahoo'})
    except:
        pass 

    # 2. NewsAPI Fallback (If Yahoo fails or returns no news)
    if not stock_obj["news"]:
        # Search specifically for the stock ticker + "stock"
        fallback_news = get_news(query=f"{ticker} stock", limit=3)
        stock_obj["news"] = fallback_news

    return stock_obj

# --- AI SUMMARIZER ---
def generate_summary(news_items, context_type):
    if not news_items: return f"No recent news found for {context_type}."
    text_data = "\n".join([f"- {n['title']}" for n in news_items])
    prompt = f"Summarize this {context_type} news into 3 short bullet points. NEWS: {text_data}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "AI Summary Unavailable."
        

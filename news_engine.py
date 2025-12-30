import yfinance as yf
from newsapi import NewsApiClient
from openai import OpenAI
import streamlit as st
import requests
import xml.etree.ElementTree as ET # Standard library for parsing Google RSS
import os

# --- CONFIGURATION ---
def get_secret(key_name):
    try:
        return st.secrets[key_name]
    except:
        return os.environ.get(key_name)

# We still keep these for the AI, even though we use Google for news now
NEWS_API_KEY = get_secret('NEWS_API_KEY')
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# --- WEATHER (Met Office) ---
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

# --- GOOGLE NEWS FETCHER (The Fix) ---
def get_google_news(query, limit=5):
    try:
        # Force UK Region (gl=GB) and English (hl=en-GB)
        # This URL returns an XML RSS feed
        url = f"https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
        response = requests.get(url, timeout=5)
        
        # Parse XML
        root = ET.fromstring(response.content)
        items = []
        
        # Iterate through news items
        for item in root.findall('./channel/item')[:limit]:
            title = item.find('title').text
            link = item.find('link').text
            pubDate = item.find('pubDate').text
            
            # Clean up title (Google often puts " - SourceName" at the end)
            source = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                source = parts[1]
                
            items.append({'title': title, 'url': link, 'source': source, 'date': pubDate})
            
        return items
    except Exception as e:
        print(f"Google News Error: {e}")
        return []

# --- STOCK DATA ---
def get_stock_data(ticker):
    stock_obj = {
        "symbol": ticker, 
        "price": "N/A", 
        "chg_1d": "0.00%", "color_1d": "off",
        "chg_1m": "0.00%", "color_1m": "off",
        "chg_1y": "0.00%", "color_1y": "off",
        "news": []
    }

    # 1. Price Data
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        
        if not hist.empty:
            curr = hist['Close'].iloc[-1]
            stock_obj["price"] = f"${curr:.2f}"
            
            def get_change(days):
                if len(hist) > days:
                    prev = hist['Close'].iloc[-(days+1)]
                    pct = ((curr - prev) / prev) * 100
                    color = "green" if pct >= 0 else "red"
                    return f"{pct:+.2f}%", color
                return "N/A", "off"

            stock_obj["chg_1d"], stock_obj["color_1d"] = get_change(1)
            stock_obj["chg_1m"], stock_obj["color_1m"] = get_change(21) 
            stock_obj["chg_1y"], stock_obj["color_1y"] = get_change(250) 
            
            # Try Yahoo news first
            if t.news:
                for n in t.news[:3]:
                    link = n.get('link') or n.get('url') or '#'
                    stock_obj["news"].append({'title': n['title'], 'url': link, 'source': 'Yahoo Finance'})
    except:
        pass 

    # 2. Google News Fallback (Much better for finding specific company news)
    if not stock_obj["news"]:
        # Query: "TICKER stock news" (e.g. "NVDA stock news")
        fallback_news = get_google_news(query=f"{ticker} stock news", limit=4)
        stock_obj["news"] = fallback_news

    return stock_obj

# --- AI SUMMARIZER ---
def generate_summary(news_items, context_type):
    if not news_items: return f"No recent news found for {context_type}."
    
    text_data = "\n".join([f"- {n['title']} ({n['source']})" for n in news_items])
    
    prompt = f"""
    You are a financial news anchor. Summarize the following stories for {context_type}.
    
    RULES:
    1. Filter out ads, promotions, or irrelevant clickbait.
    2. Focus on: Local events (for location news), Business moves (for stocks), or National headlines (for UK).
    3. Be concise. Max 3 bullet points.
    
    STORIES:
    {text_data}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "AI Summary Unavailable."
        

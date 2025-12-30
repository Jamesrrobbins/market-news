import yfinance as yf
from newsapi import NewsApiClient
from openai import OpenAI
import streamlit as st
import requests
import os
import datetime

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

# --- WEATHER (Powered by Met Office Data via Open-Meteo) ---
def get_weather(location_name):
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1&language=en&format=json"
        geo_data = requests.get(geo_url).json()
        
        if not geo_data.get('results'):
            return None
            
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        
        # 2. Weather Data (Using 'ukmo_seamless' = Met Office Global Model)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&wind_speed_unit=mph&models=ukmo_seamless"
        w_data = requests.get(weather_url).json()['current']
        
        # Helper to decode weather codes
        weather_codes = {0: "Clear Sky", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast", 45: "Fog", 51: "Drizzle", 61: "Rain", 71: "Snow", 95: "Thunderstorm"}
        condition = weather_codes.get(w_data['weather_code'], "Variable")
        
        return {
            "temp": f"{w_data['temperature_2m']}°C",
            "feels_like": f"{w_data['apparent_temperature']}°C",
            "wind": f"{w_data['wind_speed_10m']} mph",
            "humidity": f"{w_data['relative_humidity_2m']}%",
            "condition": condition,
            "source": "Met Office (UKMO)"
        }
    except Exception as e:
        return {"error": str(e)}

# --- NEWS FETCHING ---
def get_news(query=None, country=None, category=None, domains=None, limit=5):
    try:
        if domains:
            # Specific websites (Guardian, BBC, Sky)
            data = newsapi.get_everything(q=query or 'UK', domains=domains, language='en', sort_by='publishedAt')
        elif country or category:
            # Top headlines (Global)
            data = newsapi.get_top_headlines(q=query, country=country, category=category, language='en')
        else:
            # Everything (Local)
            data = newsapi.get_everything(q=query, language='en', sort_by='publishedAt')
            
        articles = data.get('articles', [])[:limit]
        return [f"{a['title']} ({a['source']['name']})" for a in articles]
    except Exception:
        return []

# --- STOCK DATA ---
def get_stock_data(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        if hist.empty: return None

        curr = hist['Close'].iloc[-1]
        
        def calc_change(days):
            if len(hist) > days:
                prev = hist['Close'].iloc[-(days+1)]
                return ((curr - prev) / prev) * 100
            return 0.0

        news_items = t.news[:3] if t.news else []
        news_titles = [n['title'] for n in news_items]
        
        return {
            "price": curr,
            "chg_1d": calc_change(1),
            "chg_1mo": calc_change(21), 
            "chg_1y": calc_change(252),
            "news": news_titles
        }
    except:
        return None

# --- AI SUMMARIZER ---
def generate_summary(text_data, context_type):
    if not text_data: return "No recent news found."
    
    prompt = f"""
    Summarize this {context_type} news into a single, flowing paragraph (approx 3-4 sentences). 
    Focus on the most impactful facts.
    
    NEWS DATA:
    {text_data}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
    

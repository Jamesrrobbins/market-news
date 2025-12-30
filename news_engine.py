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
def get_news(query=None, country=None, category=None, domains=None, limit=10):
    try:
        if domains:
            data = newsapi.get_everything(q=query or 'General', domains=domains, language='en', sort_by='publishedAt')
        elif category or country:
            data = newsapi.get_top_headlines(country=country, category=category, language='en')
        else:
            data = newsapi.get_everything(q=query, language='en', sort_by='publishedAt')
            
        articles = data.get('articles', [])[:limit]
        return [{'title': a['title'], 'source': a['source']['name'], 'url': a['url']} for a in articles]
    except Exception as e:
        print(f"News Error: {e}")
        return []

# --- STOCK DATA (With 1Y History & Analysis) ---
def get_stock_data(ticker):
    stock_obj = {
        "symbol": ticker, 
        "price": "N/A", 
        "chg_1d": "0.00%", "color_1d": "off",
        "chg_1m": "0.00%", "color_1m": "off",
        "chg_1y": "0.00%", "color_1y": "off",
        "news": []
    }

    try:
        t = yf.Ticker(ticker)
        # Fetch 1 Year of data to calculate all metrics
        hist = t.history(period="1y")
        
        if not hist.empty:
            curr = hist['Close'].iloc[-1]
            stock_obj["price"] = f"${curr:.2f}"
            
            # Helper to calc change safely
            def get_change(days):
                if len(hist) > days:
                    prev = hist['Close'].iloc[-(days+1)]
                    pct = ((curr - prev) / prev) * 100
                    color = "green" if pct >= 0 else "red"
                    return f"{pct:+.2f}%", color
                return "N/A", "off"

            stock_obj["chg_1d"], stock_obj["color_1d"] = get_change(1)
            stock_obj["chg_1m"], stock_obj["color_1m"] = get_change(21) # ~1 trading month
            stock_obj["chg_1y"], stock_obj["color_1y"] = get_change(250) # ~1 trading year
            
            if t.news:
                for n in t.news[:5]:
                    link = n.get('link') or n.get('url') or '#'
                    stock_obj["news"].append({'title': n['title'], 'url': link, 'source': 'Yahoo'})
    except:
        pass 

    # Fallback to NewsAPI if Yahoo is empty
    if not stock_obj["news"]:
        # Search for "Company Name" OR "Ticker Stock" to get better results
        fallback_news = get_news(query=f"{ticker} company stock", limit=5)
        stock_obj["news"] = fallback_news

    return stock_obj

# --- AI SUMMARIZER (Strict Analyst Mode) ---
def generate_summary(news_items, context_type):
    if not news_items: return f"No significant news found for {context_type}."
    
    text_data = "\n".join([f"- {n['title']} ({n['source']})" for n in news_items])
    
    # NEW PROMPT: Filters out ads and focuses on material events
    prompt = f"""
    You are a senior financial analyst. Review the recent news titles below for {context_type}.
    
    RULES:
    1. IGNORE any promotions, ads, "best stock to buy" lists, or generic market noise.
    2. Focus ONLY on material business developments: Earnings, Products, Legal Issues, Mergers, or significant price movement causes.
    3. If the news is just junk/ads, say "No material developments found."
    4. Format as 2-3 concise bullet points.
    
    NEWS DATA:
    {text_data}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except:
        return "AI Analysis Unavailable."
        

import requests

API_KEY = "Y05ttK9xVzqjmuDNLxpf6JL300RKHlKJm4c4960L"
API_URL = "https://api.marketaux.com/v1/news/all"

def fetch_news_and_events(symbols=None, limit=5, language="en"):
    params = {
        "api_token": API_KEY,
        "language": language,
        "limit": limit,
    }
    if symbols:
        params["symbols"] = symbols

    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        return response.json().get("data", [])
    return []
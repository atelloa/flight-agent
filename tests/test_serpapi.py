import requests
from config import SERP_API_KEY

# Test: buscar vuelos Lima → Madrid (SOLO IDA)
params = {
    "engine": "google_flights",
    "departure_id": "LIM",
    "arrival_id": "MAD",
    "outbound_date": "2026-11-15",
    "type": 2,  # NUEVO: type 2 = one way (solo ida)
    "api_key": SERP_API_KEY,
}

response = requests.get("https://serpapi.com/search", params=params)
data = response.json()

# Ver estructura
import json
print(json.dumps(data, indent=2)[:3000])
import os
from dotenv import load_dotenv
import requests

# Load the API key from .env (which Git ignores)
load_dotenv()
api_key = os.getenv("MARTA_API_KEY")

# MARTA rail real-time arrivals endpoint
url = (
    "https://developerservices.itsmarta.com:18096/itsmarta"
    "/railrealtimearrivals/developerservices/traindata"
    f"?apiKey={api_key}"
)

response = requests.get(url, timeout=30)
trains = response.json()

print(f"Success! Pulled {len(trains)} live train records.")
print("Here's the first one:")
print(trains[0])
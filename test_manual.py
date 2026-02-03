import requests
import json

# The URL where your API is running
url = "http://127.0.0.1:8000/analyze_transaction/"

# TEST CASE: The "Synthetic Ghost" Attack
# We use the specific device ID we created in generate_data.py
payload = {
    "customer_id": 1002,           # Any random customer
    "amount": 50000.0,             # High amount
    "device_id": "Android_Pixel_Shared_ID_99",  # <--- THE TRAP!
    "account_age_days": 365
}

print(f"📡 Sending Transaction: {payload['amount']} INR from Device {payload['device_id']}...")

try:
    response = requests.post(url, json=payload)
    data = response.json()

    print("\n--- ⚖️ TRIBUNAL VERDICT ---")
    print(f"Final Status: {data['status']} (Risk Score: {data['risk_score']}%)")
    print("\n--- JUDGE BREAKDOWN ---")
    print(json.dumps(data['tribunal_breakdown'], indent=4))

except Exception as e:
    print(f"Error: {e}")
    print("Is the server running? (uvicorn api:app --reload)")
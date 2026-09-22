"""
Quick manual test script for the /api/estimations/analyze endpoint.
Run this from the project root with the venv activated, while Flask is running:

    python test_analyze.py
"""
import requests

BASE_URL = "http://localhost:5000/api"

# --- Step 1: login to get a token ---
login_resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "test2@test.com",
    "password": "test123",
})
login_resp.raise_for_status()
token = login_resp.json()["token"]
print("Login OK, token acquired.")

# --- Step 2: call /estimations/analyze with mixed-case values ---
# (deliberately mixed case to test the .lower() normalization)
form_data = {
    "brand": "Maruti",
    "model": "Swift",
    "year": "2020",
    "km": "45000",
    "fuel": "Petrol",
    "transmission": "Manual",
    "city": "Pune",
    "bodyType": "Hatchback",
    "owners": "1",
}

headers = {"Authorization": f"Bearer {token}"}

# No photos attached — same as the CLI test with an empty --photos list
analyze_resp = requests.post(
    f"{BASE_URL}/estimations/analyze",
    data=form_data,
    headers=headers,
)

print("\nStatus code:", analyze_resp.status_code)
print("Response body:")
try:
    import json
    print(json.dumps(analyze_resp.json(), indent=2))
except Exception:
    print(analyze_resp.text)

# --- Step 3: verify it was actually saved by fetching history ---
history_resp = requests.get(f"{BASE_URL}/estimations", headers=headers)
print("\nHistory check — status:", history_resp.status_code)
print(json.dumps(history_resp.json(), indent=2))

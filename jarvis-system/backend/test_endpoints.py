import requests

base_url = "http://localhost:8000/api/v1"

print("--- Testing Profile ---")
print(requests.get(f"{base_url}/profile/").json())
print(requests.get(f"{base_url}/profile/academic-history").json())

print("\n--- Testing Study Session ---")
response = requests.post(f"{base_url}/study/session/start", json={"topic": "Databases"})
print(response.json())
session_id = response.json().get("session_id")

print(requests.get(f"{base_url}/study/session/status").json())
print(requests.post(f"{base_url}/study/session/end", params={"session_id": session_id}).json())

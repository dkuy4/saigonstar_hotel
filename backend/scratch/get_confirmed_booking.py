import httpx
client = httpx.Client()
resp = client.post("http://127.0.0.1:8000/api/v1/auth/login", json={"username": "letan", "password": "LeTan123#"})
token = resp.json()["token"]
res = client.get("http://127.0.0.1:8000/api/v1/bookings?status=CONFIRMED&pageSize=5", headers={"Authorization": f"Bearer {token}"})
items = res.json().get("items", [])
if items:
    print("Keys:", items[0].keys())
    print("Sample:", items[0])
else:
    print("No items")

import requests

dlhd_id = "661"  # İstediğin stream ID
url = f"https://daddylivehd1.online/embed/stream-{dlhd_id}.php"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print(response.text)
else:
    print(f"Hata: Sayfa alınamadı (Status Code: {response.status_code})")

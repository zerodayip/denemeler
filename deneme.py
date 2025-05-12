import requests
from bs4 import BeautifulSoup

dlhd_id = "661"
url = f"https://daddylivehd1.online/embed/stream-{dlhd_id}.php"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

try:
    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup.prettify())  # Tüm HTML'yi düzgün formatta yazdırır
    else:
        print(f"Hata: Sayfa alınamadı. HTTP {response.status_code}")

except Exception as e:
    print(f"İstek sırasında hata oluştu: {e}")

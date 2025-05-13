import os
import time
import requests
from typing import Callable, Dict, Optional

MIRRORS = [
    "https://ppv.land",
    "https://freeppv.fun",
    "https://ppv.wtf",
    "https://ppvs.su"
]

# Yayın filtreleri
def filter_24_7(stream):
    month_ago = time.time() - 86400 * 30
    return stream.get("starts_at", 0) < month_ago

def filter_event(stream):
    month_ago = time.time() - 86400 * 30
    return stream.get("starts_at", 0) > month_ago

M3U_LIST: Dict[str, Optional[Callable[[dict], bool]]] = {
    "full": None,
    "24-7": filter_24_7,
    "event": filter_event
}

# Klasörleri oluştur
os.makedirs("m3u", exist_ok=True)

class Ppv:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def is_working(self) -> bool:
        """Mirror çalışıyor mu test et."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def generate_m3u(self, filter_func: Optional[Callable[[dict], bool]] = None) -> str:
        """M3U çıktısı oluştur."""
        try:
            response = requests.get(f"{self.base_url}/api/streams", timeout=10)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise ValueError(f"API beklenen listeyi döndürmedi: {data}")

            streams = data

            if filter_func:
                streams = list(filter(filter_func, streams))

            # M3U çıktısı
            m3u = "#EXTM3U\n"
            for stream in streams:
                m3u += (
                    f'#EXTINF:-1 tvg-id="{stream["id"]}" tvg-name="{stream["name"]}",{stream["name"]}\n'
                    f'{stream["url"]}\n'
                )

            return m3u

        except Exception as e:
            print(f"[HATA] Yayınlar alınamadı: {e}")
            raise

def main():
    for mirror in MIRRORS:
        ppv = Ppv(mirror)
        if ppv.is_working():
            print(f"[✓] Mirror çalışıyor: {ppv.base_url}")
        else:
            print(f"[✗] Mirror çalışmıyor: {ppv.base_url}, sıradakine geçiliyor...")
            continue

        for name, criteria in M3U_LIST.items():
            try:
                print(f'[•] M3U "{name}" oluşturuluyor...')
                m3u_data = ppv.generate_m3u(criteria)
                with open(f"m3u/{name}.m3u", "w", encoding="utf-8") as m3u_file:
                    m3u_file.write(m3u_data)
                print(f"[✓] {name} başarıyla kaydedildi.")
            except Exception as e:
                print(f"[HATA] M3U '{name}' oluşturulamadı: {e}")

        break  # İlk çalışan mirror ile işlem tamamlandı

if __name__ == "__main__":
    main()

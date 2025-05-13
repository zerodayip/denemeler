import requests
import os
from typing import Callable, Optional
import time

# Mirror URL'leri
MIRRORS = [
    "https://ppv.land",
    "https://freeppv.fun",
    "https://ppv.wtf",
    "https://ppvs.su"
]

# M3U Listesi Filtreleme
m3uList = {
    "full": None,
    "24-7": lambda stream: (time.time() - stream['starts_at']) > 86400 * 30,  # 30 gün önceki yayınlar
    "event": lambda stream: (time.time() - stream['starts_at']) < 86400 * 30  # 30 gün içinde başlayan yayınlar
}

class Ppv:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def is_working(self) -> bool:
        """Mirror'ün çalışıp çalışmadığını kontrol et."""
        try:
            response = requests.get(f"{self.base_url}/api/streams", timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'streams' in data:
                return True
            return False
        except Exception as e:
            print(f"[HATA] Mirror çalışmıyor: {self.base_url}, {e}")
            return False
    
    def generate_m3u(self, filter_func: Optional[Callable[[dict], bool]] = None) -> str:
        """M3U çıktısı oluştur."""
        try:
            response = requests.get(f"{self.base_url}/api/streams", timeout=10)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict) or 'streams' not in data:
                raise ValueError(f"API beklenen formatta veri döndürmedi: {data}")

            # İç içe geçmiş 'streams' listesini al
            all_streams = []
            for category in data['streams']:
                if 'streams' in category:
                    all_streams.extend(category['streams'])

            # Eğer filtre fonksiyonu varsa, filtre uygula
            if filter_func:
                all_streams = list(filter(filter_func, all_streams))

            # M3U çıktısı oluştur
            m3u = "#EXTM3U\n"
            for stream in all_streams:
                m3u += (
                    f'#EXTINF:-1 tvg-id="{stream["id"]}" tvg-name="{stream["name"]}",{stream["name"]}\n'
                    f'{stream["iframe"]}\n'
                )

            return m3u

        except Exception as e:
            print(f"[HATA] Yayınlar alınamadı: {e}")
            raise


def create_directories():
    """Gerekli dizinleri oluştur."""
    os.makedirs("m3u", exist_ok=True)


def save_to_file(name: str, m3u_data: str):
    """M3U dosyasını kaydet."""
    with open(f"m3u/{name}.m3u", "w") as m3u_file:
        m3u_file.write(m3u_data)


def main():
    create_directories()
    
    for mirror_url in MIRRORS:
        ppv = Ppv(mirror_url)
        if ppv.is_working():
            print(f"Mirror {mirror_url} çalışıyor.")
        else:
            print(f"Mirror {mirror_url} çalışmıyor, sıradakine geçiliyor...")
            continue
        
        # M3U'yu oluştur
        for name, filter_func in m3uList.items():
            print(f'M3U "{name}" oluşturuluyor...')
            try:
                m3u_data = ppv.generate_m3u(filter_func)
                save_to_file(name, m3u_data)
                print(f'M3U "{name}" başarıyla oluşturuldu ve kaydedildi.')
            except Exception as e:
                print(f"[HATA] M3U '{name}' oluşturulamadı: {e}")
        
        break  # Sadece bir mirror'u kontrol et ve işlemi bitir.

if __name__ == "__main__":
    main()

import httpx
import asyncio

async def get_m3u8_links(url):
    async with httpx.AsyncClient() as client:
        # Sayfayı istekle yükle
        response = await client.get(url)
        
        # Ağ istekleri yapılırken tüm içerikleri kontrol et
        print("Sayfa yüklendi, tüm istekleri izliyoruz...")
        
        m3u8_links = []

        # Tüm istekleri (request) ve yanıtları (response) takip et
        async with client.stream("GET", url) as request:
            async for line in request.aiter_lines():
                if ".m3u8" in line:  # .m3u8 içeren satırları kontrol et
                    print(f"Bulunan M3U8 Bağlantısı: {line.strip()}")
                    m3u8_links.append(line.strip())

        # Eğer .m3u8 bağlantıları bulunduysa, onları yazdır
        if m3u8_links:
            print("\n✔️ Bulunan M3U8 bağlantıları:")
            for link in m3u8_links:
                print(link)
        else:
            print("\n❌ M3U8 bağlantısı bulunamadı.")
    
    return m3u8_links

# Ana fonksiyon
async def main():
    # İlgili URL'yi burada belirt
    url = "https://cdn.livetv852.me/export/webplayer.iframe.php?t=alieztv&c=235414&eid=290899339&lid=2690363&lang=en&m&dmn="
    
    # M3U8 bağlantılarını al
    m3u8_links = await get_m3u8_links(url)
    
    # Eğer .m3u8 bağlantısı bulunduysa
    if m3u8_links:
        print("\n✔️ İşlem tamamlandı ve M3U8 bağlantıları başarıyla alındı.")
    else:
        print("\n❌ İşlem tamamlandı ancak M3U8 bağlantısı bulunamadı.")

# Başlat
if __name__ == "__main__":
    asyncio.run(main())

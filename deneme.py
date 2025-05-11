from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Hedef URL
    page.goto("https://cdn.livetv852.me/export/webplayer.iframe.php?t=alieztv&c=235414&eid=290899339&lid=2690363&lang=en&m&dmn=")

    # Bulunan linkleri burada tut
    m3u8_links = []

    # Yanıtları incele
    def handle_response(response):
        url = response.url
        if ".m3u8" in url and url not in m3u8_links:
            print("🎯 Bulunan M3U8 bağlantısı:", url)
            m3u8_links.append(url)

    # Yanıt olayını dinle
    page.on("response", handle_response)

    # Yeterli süre bekle (oynatıcının yüklenmesi için)
    page.wait_for_timeout(10000)

    browser.close()

    # Sonuçları yazdır
    if m3u8_links:
        print("\n✔️ Bulunan ilk M3U8 bağlantısı:\n", m3u8_links[0])
    else:
        print("\n❌ M3U8 bağlantısı bulunamadı.")

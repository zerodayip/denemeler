from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://cdn.livetv852.me/export/webplayer.iframe.php?t=alieztv&c=...")
    
    # Ağ isteklerini dinle
    m3u8_url = None

    def log_request(response):
        url = response.url
        if ".m3u8" in url:
            print("🎯 Bulunan M3U8:", url)
            nonlocal m3u8_url
            m3u8_url = url

    page.on("response", log_request)

    page.wait_for_timeout(10000)
    browser.close()


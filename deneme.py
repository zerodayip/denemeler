from playwright.sync_api import sync_playwright

# Playwright'ı kullanarak sayfa içeriğini çekme
with sync_playwright() as p:
    # Headless modda Chromium tarayıcısını başlatıyoruz
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Sayfayı açıyoruz
    url = "https://daddylivehd1.online/embed/stream-661.php"
    page.goto(url)
    
    # Sayfanın HTML içeriğini alıyoruz
    html_content = page.content()
    
    # HTML'yi yazdırıyoruz
    print(html_content)
    
    # Tarayıcıyı kapatıyoruz
    browser.close()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # Tarayıcıyı başlatıyoruz
    page = browser.new_page()
    
    # URL'yi açıyoruz
    page.goto('https://daddylivehd1.online/embed/stream-661.php')
    
    # Sayfanın HTML içeriğini alıyoruz
    html_content = page.content()
    
    print(html_content)  # Sayfanın HTML içeriğini yazdırıyoruz
    
    browser.close()  # Tarayıcıyı kapatıyoruz

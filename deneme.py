from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Headless modda Chrome tarayıcısını çalıştırmak için
chrome_options = Options()
chrome_options.add_argument("--headless")  # Tarayıcı arayüzünü göstermemek için
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Chrome WebDriver'ı başlat
driver = webdriver.Chrome(options=chrome_options)

# URL'yi aç
url = "https://daddylivehd1.online/embed/stream-661.php"
driver.get(url)

# Sayfanın tam olarak yüklenmesi için biraz bekleyelim
time.sleep(5)

# Sayfanın HTML içeriğini al
html_content = driver.page_source

# HTML'yi terminalde yazdır
print(html_content)

# Tarayıcıyı kapat
driver.quit()

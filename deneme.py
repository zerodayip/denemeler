from playwright.sync_api import sync_playwright
import os
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup

def html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}

    # Tam tarih başlığı "Tuesday 06th May 2025 – Schedule Time UK GMT"
    full_heading = soup.find('strong', string=re.compile(r'\w+ \d{2}(st|nd|rd|th) \w+ \d{4}\s+–\s+Schedule Time', re.IGNORECASE))
    if not full_heading:
        print("UYARI: Tarih bilgisi bulunamadı!")
        return {}

    date_text = full_heading.get_text(strip=True)
    result[date_text] = {}

    for h2 in soup.find_all('h2'):
        category = h2.get_text(strip=True)

        # Boş veya tekrar eden başlıkları atla
        if category.lower().startswith("daddylivehd") or category == date_text:
            continue

        events = []
        for tag in h2.find_all_next('strong'):
            if tag.find_previous('h2') != h2:
                break

            full_text = tag.get_text(" ", strip=True)
            match = re.match(r'(\d{2}:\d{2})\s+(.*?)(?=(https?|$))', full_text)
            if not match:
                continue

            event_time = match.group(1)
            event_info = match.group(2).strip()

            channels = []
            for a in tag.find_all('a', href=True):
                href = a['href']
                name = a.get_text(strip=True)
                id_match = re.search(r'stream-(\d+)\.php', href)
                if id_match:
                    channel_id = id_match.group(1)
                    clean_name = re.sub(r'\s*\(CH-\d+\)$', '', name)
                    channels.append({
                        "channel_name": clean_name,
                        "channel_id": channel_id
                    })

            # Event'ten kanal isimlerini sil
            if channels:
                first_channel = channels[0]['channel_name']
                event_info = event_info.split(first_channel)[0].strip()
                event_info = re.sub(r'\|$', '', event_info).strip()

            events.append({
                "time": event_time,
                "event": event_info,
                "channels": channels
            })

        if events:
            result[date_text][category] = events

    return result

def modify_json_file(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Tarih anahtarlarını koru, sadece yapıyı yeniden yaz
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"JSON dosyası güncellendi ve kaydedildi: {json_file_path}")

def extract_schedule_container():
    url = "https://daddylivehd1.click/"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_output = os.path.join(script_dir, "schedule.json")

    print(f"{url} sayfasına erişiliyor, ana program içeriği çekiliyor...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Sayfaya gidiliyor...")
            page.goto(url)
            print("Sayfanın tam yüklenmesi bekleniyor...")
            page.wait_for_timeout(10000)

            schedule_content = page.content()

            if not schedule_content:
                print("UYARI: Sayfa içeriği boş!")
                return False

            print("HTML içerik JSON formatına dönüştürülüyor...")
            json_data = html_to_json(schedule_content)

            with open(json_output, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)

            print(f"JSON verileri kaydedildi: {json_output}")

            modify_json_file(json_output)
            browser.close()
            return True

        except Exception as e:
            print(f"HATA: {str(e)}")
            return False

if __name__ == "__main__":
    success = extract_schedule_container()
    if not success:
        exit(1)

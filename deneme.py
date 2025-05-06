from playwright.sync_api import sync_playwright
import os
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup

def html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}

    # Tarih bilgisini çek
    date_strong = soup.find('strong', string=re.compile(r'\w+ \d{2}(st|nd|rd|th) \w+ \d{4}', re.IGNORECASE))
    if not date_strong:
        print("UYARI: Tarih bilgisi bulunamadı!")
        return {}

    date_text = date_strong.get_text(strip=True).split('–')[0].strip()
    result[date_text] = {}

    # Tüm kategorileri tara (örneğin TV Shows, Sports Events vs.)
    category_headers = soup.find_all('h2')
    for header in category_headers:
        category = header.get_text(strip=True)
        if not category:
            continue

        result[date_text][category] = []

        for tag in header.find_all_next('strong'):
            # Eğer bir sonraki <h2>'ye geldiysek kategoriyi bitir
            if tag.find_previous('h2') != header:
                break

            full_text = tag.get_text(" ", strip=True)
            match = re.match(r'(\d{2}:\d{2})\s+(.*)', full_text)
            if not match:
                continue

            event_time = match.group(1)
            event_info = match.group(2).strip()

            # '|' sembolüyle gelen kanal isimlerini ayıkla
            if '|' in event_info:
                event_info = event_info.split('|')[0].strip()

            # Linkli kanal bilgilerini çıkar
            channels = []
            first_channel_found = False
            for a in tag.find_all('a', href=True):
                href = a['href']
                name = a.get_text(strip=True)
                id_match = re.search(r'stream-(\d+)\.php', href)
                if id_match:
                    channel_id = id_match.group(1)
                    clean_name = re.sub(r'\s*\(CH-\d+\)$', '', name)

                    if not first_channel_found:
                        # Event'teki ilk kanal ismini yakalayınca oradan itibaren kırp
                        split_index = event_info.find(name)
                        if split_index != -1:
                            event_info = event_info[:split_index].strip()
                        event_info = re.sub(r'\(CH-\d+\)', '', event_info).strip()
                        first_channel_found = True

                    channels.append({
                        "channel_name": clean_name,
                        "channel_id": channel_id
                    })

            result[date_text][category].append({
                "time": event_time,
                "event": event_info,
                "channels": channels
            })

    return result

def modify_json_file(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    current_month = datetime.now().strftime("%B")

    for date in list(data.keys()):
        match = re.match(r"(\w+\s\d+)(st|nd|rd|th)\s(\w+)\s(\d{4})", date)
        if match:
            day_part = match.group(1)
            suffix = match.group(2)
            month_part = match.group(3)
            year_part = match.group(4)
            new_date = f"{day_part}{suffix} {month_part} {year_part}"
            data[new_date] = data.pop(date)

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

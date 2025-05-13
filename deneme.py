import os, time, json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

MIRRORS = [
    "https://ppv.land",
    "https://freeppv.fun",
    "https://ppv.wtf",
    "https://ppvs.su"
]

FILTERS = {
    "full": None,
    "24-7": lambda s: s.get("starts_at", 0) < time.time() - 86400 * 30,
    "event": lambda s: s.get("starts_at", 0) >= time.time() - 86400 * 30,
}

def get_working_mirror():
    for url in MIRRORS:
        try:
            r = requests.get(f"{url}/api/streams", timeout=5)
            if r.ok and "streams" in r.text:
                return url
        except:
            pass
    return None

def extract_m3u8_from_iframe(iframe_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(iframe_url)
        time.sleep(3)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["script", "source"]):
            if tag and ".m3u8" in str(tag):
                return str(tag).split("http")[1].split(".m3u8")[0]
    except Exception as e:
        print("Iframe parsing error:", e)
    finally:
        driver.quit()

    return None

def generate_m3u(streams):
    lines = ["#EXTM3U"]
    for stream in streams:
        title = stream.get("name", "No Title")
        m3u8 = extract_m3u8_from_iframe(stream["iframe"])
        if m3u8:
            lines.append(f'#EXTINF:-1 tvg-name="{title}",{title}')
            lines.append(f"http{m3u8}.m3u8")
    return "\n".join(lines)

def main():
    os.makedirs("m3u", exist_ok=True)
    base = get_working_mirror()
    if not base:
        print("No mirror working.")
        return

    r = requests.get(f"{base}/api/streams")
    data = r.json()

    all_streams = []
    for group in data.get("streams", []):
        all_streams.extend(group.get("streams", []))

    for name, func in FILTERS.items():
        filtered = all_streams if func is None else list(filter(func, all_streams))
        if not filtered:
            print(f"[!] {name} listesi boş.")
            continue
        print(f"[+] {name} listesi hazırlanıyor: {len(filtered)} yayın")
        m3u_content = generate_m3u(filtered)
        with open(f"m3u/{name}.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)

if __name__ == "__main__":
    main()

# ppv_updater.py

import os
import time
import json
import asyncio
import aiohttp
from typing import Callable, Optional
from playwright.async_api import async_playwright

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


def ensure_dirs():
    os.makedirs("m3u", exist_ok=True)


async def fetch_streams(session, mirror):
    try:
        async with session.get(f"{mirror}/api/streams") as resp:
            data = await resp.json()
            return data.get("streams", [])
    except Exception as e:
        print(f"[✗] {mirror} mirror erişilemedi: {e}")
        return None


async def extract_m3u8_link(iframe_url, playwright):
    try:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(iframe_url, timeout=20000)
        content = await page.content()
        m3u8_links = [line for line in content.split('"') if ".m3u8" in line]
        await browser.close()
        return m3u8_links[0] if m3u8_links else None
    except Exception as e:
        print(f"[HATA] .m3u8 alınamadı ({iframe_url}): {e}")
        return None


async def build_m3u_category(name: str, streams: list, filter_fn: Optional[Callable], playwright):
    lines = ["#EXTM3U"]

    count = 0
    for stream in streams:
        substreams = stream.get("streams", [])
        for s in substreams:
            if filter_fn and not filter_fn(s):
                continue

            title = s.get("name", "No Name")
            logo = s.get("poster", "")
            group = stream.get("category", "Unknown")
            iframe_url = s.get("iframe")

            m3u8_link = await extract_m3u8_link(iframe_url, playwright)
            if not m3u8_link:
                continue

            lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{title}')
            lines.append(m3u8_link)
            count += 1

    if count:
        with open(f"m3u/{name}.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[✓] {name}.m3u ({count} yayın) kaydedildi.")
    else:
        print(f"[!] {name} kategorisi için uygun yayın bulunamadı.")


async def main():
    ensure_dirs()
    async with aiohttp.ClientSession() as session:
        async with async_playwright() as playwright:
            for mirror in MIRRORS:
                streams = await fetch_streams(session, mirror)
                if streams:
                    print(f"[✓] Aktif mirror bulundu: {mirror}")
                    for name, filt in FILTERS.items():
                        print(f"[•] M3U oluşturuluyor: {name}")
                        await build_m3u_category(name, streams, filt, playwright)
                    break
            else:
                print("[✗] Hiçbir mirror çalışmıyor.")

if __name__ == "__main__":
    asyncio.run(main())

import json
import requests
import time
import re

# --------- BÖLÜM 1: Canlı TV Verileri ---------
url_kategoriler = "https://service-media-catalog.clusters.pluto.tv/v1/main-categories?includeImages=svg"
url_kanallar = "https://service-channels.clusters.pluto.tv/v2/guide/channels?channelIds=&offset=0&limit=1000&sort=number%3Aasc"

headers1 = {}
headers2 = {}

toplam_sure_baslangic = time.time()
sure_baslangic = time.time()

# Kategorileri çek
cevap1 = requests.get(url_kategoriler, headers=headers1)
kategoriler = {}
if cevap1.status_code == 200:
    veriler1 = cevap1.json()
    kategoriler = {item.get("id"): item.get("name") for item in veriler1.get("data", [])}
else:
    print(f"HATA: Kategori isteği başarısız oldu ({cevap1.status_code})")

# Kanalları çek
cevap2 = requests.get(url_kanallar, headers=headers2)
kanallar = []
ozet_bilgi = {}
if cevap2.status_code == 200:
    veriler2 = cevap2.json()
    kanallar = [
        {
            "isim": item.get("name"),
            "kategoriIDler": item.get("categoryIDs"),
            "ozet": item.get("summary"),
            "hash": item.get("hash")
        }
        for item in veriler2.get("data", [])
    ]
    ozet_bilgi = {
        "Toplam Kanal Sayısı": len(veriler2.get("data", [])),
        "Toplam Kategori Sayısı": len(kategoriler)
    }
else:
    print(f"HATA: Kanal isteği başarısız oldu ({cevap2.status_code})")

# Yapılandırılmış canlı TV verisi
canli_tv = {"Özet": ozet_bilgi, "Kategoriler": {}}

for kanal in kanallar:
    for kategori_id in kanal["kategoriIDler"]:
        kategori_adi = kategoriler.get(kategori_id, "Bilinmeyen Kategori")
        if kategori_adi not in canli_tv["Kategoriler"]:
            canli_tv["Kategoriler"][kategori_adi] = {}
        canli_tv["Kategoriler"][kategori_adi][kanal["isim"]] = {
            "Özet": kanal["ozet"],
            "Hash": kanal["hash"]
        }

sure_bitis = time.time()
canli_tv["Özet"]["Çalışma Süresi (sn)"] = round(sure_bitis - sure_baslangic, 2)

# --------- BÖLÜM 2: İsteğe Bağlı (OnDemand) İçerik ---------
def slugdan_yil_cek(slug):
    eslesme = re.search(r'-\d{4}-', slug)
    if eslesme:
        return eslesme.group(0)[1:5]
    return None

def icerik_getir(alt_kategori_id):
    url_ondemand = f"https://service-vod.clusters.pluto.tv/v4/vod/categories/{alt_kategori_id}/items?offset=30&page=1"
    cevap = requests.get(url_ondemand)
    icerikler = []

    if cevap.status_code == 200:
        for item in cevap.json().get("items", []):
            tur = item.get("type")
            baslik = item.get("name")
            aciklama = item.get("description")
            icerik_id = item.get("_id")
            siniflama = item.get("rating")
            turu = item.get("genre")
            slug = item.get("slug", "")

            yil = slugdan_yil_cek(slug) if tur == "movie" else None
            if tur == "movie":
                link = f"https://pluto.tv/latam/on-demand/movies/{icerik_id}"
                detay = f"https://pluto.tv/latam/on-demand/movies/{icerik_id}/details"
            elif tur == "series":
                link = f"https://pluto.tv/latam/search/details/series/{icerik_id}/season/1"
                detay = None
            else:
                link = detay = None

            icerikler.append({
                "Başlık": baslik,
                "Yıl": yil,
                "Açıklama": aciklama,
                "Alt Kategori ID": alt_kategori_id,
                "Bağlantı": link,
                "Detay Bağlantısı": detay,
                "Tür": tur,
                "Sınıflandırma": siniflama,
                "Türü": turu
            })
    else:
        print(f"HATA: Alt kategori {alt_kategori_id} içeriği alınamadı ({cevap.status_code})")
    return icerikler

# Kategori verileri
cevap_ana = requests.get(url_kategoriler)
ana_kategoriler = cevap_ana.json().get("data", []) if cevap_ana.status_code == 200 else []

url_alt_kategoriler = "https://service-vod.clusters.pluto.tv/v4/vod/categories?includeItems=false&includeCategoryFields=iconSvg&offset=1000&page=1&sort=number%3Aasc"
cevap_alt = requests.get(url_alt_kategoriler)
alt_kategoriler = cevap_alt.json().get("categories", []) if cevap_alt.status_code == 200 else []

ondemand_baslangic = time.time()
istege_bagli = {}

for ana in ana_kategoriler:
    ana_id = ana.get("id")
    ana_ad = ana.get("name")
    istege_bagli[ana_ad] = {}

    for alt in alt_kategoriler:
        alt_ids = [a.get("categoryID") for a in alt.get("mainCategories", [])]
        if ana_id in alt_ids:
            alt_ad = alt.get("name")
            alt_id = alt.get("_id")
            icerikler = icerik_getir(alt_id)
            istege_bagli[ana_ad][alt_ad] = icerikler

ondemand_bitis = time.time()
calisma_suresi_toplam = round(time.time() - toplam_sure_baslangic, 2)

# --------- Final JSON ---------
json_sonuc = {
    "Genel Özet": {
        "Toplam Çalışma Süresi (sn)": calisma_suresi_toplam
    },
    "Canlı TV": canli_tv,
    "İsteğe Bağlı İçerik": istege_bagli
}

# Dosyaya yaz
with open("plutotv_scraping_TR.json", "w", encoding="utf-8") as f:
    json.dump(json_sonuc, f, indent=4, ensure_ascii=False)

# Konsola yazdır
print(json.dumps(json_sonuc, indent=4, ensure_ascii=False))

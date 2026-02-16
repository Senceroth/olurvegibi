import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
HAFIZA_DOSYASI = "hafiza_eurogamer.txt"

def hafiza_oku():
    if not os.path.exists(HAFIZA_DOSYASI): return []
    with open(HAFIZA_DOSYASI, "r") as f:
        return f.read().splitlines()

def hafiza_yaz(veri):
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{veri}\n")

def telegram_gonder(mesaj):
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def haberleri_kontrol_et():
    url = "https://www.eurogamer.net/feed/news"
    headers = {"User-Agent": "Mozilla/5.0"}
    eski_haberler = hafiza_oku()
    
    print("Eurogamer taranıyor...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            haberler = soup.find_all("entry") or soup.find_all("item")
            
            for haber in haberler[:10]:
                try:
                    haberi_id = (haber.find("id") or haber.find("guid") or haber.find("link")).text.strip()
                    baslik = haber.find("title").text.strip()
                    
                    if haberi_id not in eski_haberler:
                        link_tag = haber.find("link")
                        link = link_tag.get("href") if link_tag.has_attr("href") else link_tag.text
                        
                        mesaj = f"📰 *YENİ HABER (Eurogamer)*\n\n*{baslik}*\n\n[Oku]({link})"
                        telegram_gonder(mesaj)
                        print(f"YENİ: {baslik}")
                        
                        hafiza_yaz(haberi_id)
                        eski_haberler.append(haberi_id)
                    else:
                        # LOGLARA EKLEDİK: Artık neyi geçtiğini göreceksin
                        print(f"Eski haber, geçiliyor: {baslik[:50]}...")
                except: continue
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    haberleri_kontrol_et()

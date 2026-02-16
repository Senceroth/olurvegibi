import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta, timezone

# GITHUB'DAN GELECEK ŞİFRELER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")

def telegram_gonder(mesaj):
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def haberleri_kontrol_et():
    # Eurogamer'ın resmi RSS beslemesi (En güncel ve tarihli veri buradadır)
    url = "https://www.eurogamer.net/feed/news"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # XML verisini okuyoruz
            soup = BeautifulSoup(response.content, "xml")
            haberler = soup.find_all("entry")
            
            # ŞU ANKİ ZAMAN (UTC)
            simdi = datetime.now(timezone.utc)
            
            for haber in haberler:
                # Haber Tarihini Al (Örn: 2024-02-05T14:30:00Z)
                tarih_str = haber.find("published").text
                # Tarihi Python formatına çevir
                tarih_obj = datetime.fromisoformat(tarih_str.replace('Z', '+00:00'))
                
                # EĞER SON 45 DAKİKA İÇİNDE YAYINLANDIYSA
                # (Bot her 30 dk'da bir çalışacağı için yakalar)
                fark = simdi - tarih_obj
                if fark < timedelta(minutes=45):
                    baslik = haber.find("title").text
                    link = haber.find("link")['href']
                    
                    mesaj = f"📰 *YENİ HABER (Eurogamer)*\n\n*{baslik}*\n\n[Haberi Oku]({link})"
                    telegram_gonder(mesaj)
                    print(f"Haber gönderildi: {baslik}")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    haberleri_kontrol_et()
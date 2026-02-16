import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta, timezone

# GITHUB'DAN GELECEK ŞİFRELER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")

# TAKİP EDİLECEK KANALLAR
# Buraya istediğin kadar kanal ekleyebilirsin
KANALLAR = [
    "https://www.youtube.com/@GamingBolt",
    "https://www.youtube.com/@IGN",
    "https://www.youtube.com/@PlayStation"
]

def telegram_gonder(mesaj):
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def kanal_rss_bul(kanal_url):
    # Linki temizle (/videos kısmını at)
    base_url = kanal_url.split("/videos")[0]
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US"}
    cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en+FX+419'}
    
    try:
        # Kanalın ana sayfasına gidip gizli 'Channel ID'yi buluyoruz
        resp = requests.get(base_url, headers=headers, cookies=cookies, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Meta etiketinden ID bul (YouTube'un kimlik kartı)
        meta = soup.find("meta", {"itemprop": "channelId"})
        if meta:
            channel_id = meta['content']
            # YouTube'un gizli RSS linkini oluştur
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        return None
    except: return None

def videolari_kontrol_et():
    # ŞU ANKİ ZAMAN (UTC - Evrensel Saat)
    simdi = datetime.now(timezone.utc)
    
    for kanal_linki in KANALLAR:
        rss_url = kanal_rss_bul(kanal_linki)
        if not rss_url: continue
        
        try:
            resp = requests.get(rss_url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "xml")
                videolar = soup.find_all("entry")
                
                # Sadece en son videoya bakmak yeterli
                if videolar:
                    video = videolar[0]
                    # Tarih formatı: 2024-02-05T15:30:00+00:00
                    tarih_str = video.find("published").text
                    tarih_obj = datetime.fromisoformat(tarih_str)
                    
                    # EĞER SON 15 DAKİKA İÇİNDE YAYINLANDIYSA (Güncellendi)
                    # (Bot her 10 dk'da bir çalışacağı için bu süre idealdir)
                    fark = simdi - tarih_obj
                    if fark < timedelta(minutes=15):
                        baslik = video.find("title").text
                        link = video.find("link")['href']
                        kanal_adi = video.find("author").find("name").text
                        
                        mesaj = f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n*{baslik}*\n\n[İzle]({link})"
                        telegram_gonder(mesaj)
                        print(f"Video gönderildi: {baslik}")
                    
        except Exception as e:
            print(f"Hata ({kanal_linki}): {e}")

if __name__ == "__main__":
    videolari_kontrol_et()

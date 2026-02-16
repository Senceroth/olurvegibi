import requests
from bs4 import BeautifulSoup
import os

# GITHUB'DAN GELECEK ŞİFRELER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
HAFIZA_DOSYASI = "hafiza_youtube.txt"

# TAKİP EDİLECEK KANALLAR
KANALLAR = [
    "https://www.youtube.com/@GamingBolt",
    "https://www.youtube.com/@IGN",
    "https://www.youtube.com/@PlayStation"
]

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

def kanal_rss_bul(kanal_url):
    # Linki temizle (/videos kısmını at)
    base_url = kanal_url.split("/videos")[0]
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US"}
    cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en+FX+419'}
    
    try:
        # Kanalın ana sayfasına gidip gizli 'Channel ID'yi buluyoruz
        resp = requests.get(base_url, headers=headers, cookies=cookies, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Meta etiketinden ID bul
        meta = soup.find("meta", {"itemprop": "channelId"})
        if meta:
            channel_id = meta['content']
            # YouTube'un gizli RSS linkini oluştur
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        return None
    except: return None

def videolari_kontrol_et():
    # Hafızadaki eski video ID'lerini oku
    eski_videolar = hafiza_oku()
    
    for kanal_linki in KANALLAR:
        rss_url = kanal_rss_bul(kanal_linki)
        if not rss_url: continue
        
        try:
            resp = requests.get(rss_url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "xml")
                # En son videoyu al (entry)
                video = soup.find("entry")
                
                if video:
                    video_id = video.find("videoId").text
                    
                    # EĞER BU VİDEO ID'Sİ HAFIZADA YOKSA -> YENİDİR!
                    if video_id not in eski_videolar:
                        baslik = video.find("title").text
                        link = video.find("link")['href']
                        kanal_adi = video.find("author").find("name").text
                        
                        mesaj = f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n*{baslik}*\n\n[İzle]({link})"
                        telegram_gonder(mesaj)
                        print(f"Video gönderildi: {baslik}")
                        
                        # Hafızaya kaydet
                        hafiza_yaz(video_id)
                        eski_videolar.append(video_id)
                    
        except Exception as e:
            print(f"Hata ({kanal_linki}): {e}")

if __name__ == "__main__":
    videolari_kontrol_et()

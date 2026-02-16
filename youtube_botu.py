import requests
from bs4 import BeautifulSoup
import os
import re

# GITHUB SECRETS
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
HAFIZA_DOSYASI = "hafiza_youtube.txt"

# Takip edilecek kanallar
KANALLAR = [
    "https://www.youtube.com/@GamingBolt",
    "https://www.youtube.com/@IGN",
    "https://www.youtube.com/@PlayStation"
]

def hafiza_oku():
    if not os.path.exists(HAFIZA_DOSYASI):
        return []
    with open(HAFIZA_DOSYASI, "r") as f:
        return f.read().splitlines()

def hafiza_yaz(veri):
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{veri}\n")

def telegram_gonder(mesaj):
    if not TOKEN or not CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def kanal_rss_bul(kanal_url):
    """Kanal URL'sinden RSS beslemesini bulmak için çoklu yöntem kullanır."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    # YouTube çerez onayı için gerekli
    cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en+FX+419'}
    
    try:
        # /videos kısmını temizle
        clean_url = kanal_url.split("/videos")[0]
        resp = requests.get(clean_url, headers=headers, cookies=cookies, timeout=15)
        html = resp.text
        
        # 1. Yöntem: Meta etiketinden Channel ID ara
        soup = BeautifulSoup(html, "html.parser")
        meta = soup.find("meta", {"itemprop": "channelId"})
        if meta:
            cid = meta['content']
            print(f"ID Bulundu (Meta): {cid}")
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        
        # 2. Yöntem: Sayfa kaynağından Regex ile ID ara
        match = re.search(r"\"channelId\":\"(UC[^\"]+)\"", html)
        if match:
            cid = match.group(1)
            print(f"ID Bulundu (Regex): {cid}")
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
            
        return None
    except Exception as e:
        print(f"RSS Arama Hatası ({kanal_url}): {e}")
        return None

def videolari_kontrol_et():
    eski_videolar = hafiza_oku()
    print(f"Hafızadaki eski video sayısı: {len(eski_videolar)}")
    
    if not KANALLAR:
        print("Hata: Kanal listesi boş!")
        return

    for url in KANALLAR:
        print(f"\n--- {url} kontrol ediliyor ---")
        rss_url = kanal_rss_bul(url)
        
        if not rss_url:
            print(f"Hata: RSS bağlantısı oluşturulamadı: {url}")
            continue
            
        try:
            resp = requests.get(rss_url, timeout=15)
            if resp.status_code != 200:
                print(f"Hata: RSS çekilemedi (Kod: {resp.status_code})")
                continue
                
            soup = BeautifulSoup(resp.content, "xml")
            videolar = soup.find_all("entry")
            
            if not videolar:
                print("Kanalda henüz video bulunamadı.")
                continue
                
            # En son videoyu al
            video = videolar[0]
            v_id = video.find("yt:videoId").text if video.find("yt:videoId") else video.find("id").text
            v_id = v_id.replace("yt:video:", "") # Bazı ID'ler bu ön ekle gelir
            
            if v_id not in eski_videolar:
                baslik = video.find("title").text.strip()
                v_link = video.find("link")['href'] if video.find("link") else f"https://www.youtube.com/watch?v={v_id}"
                kanal_adi = video.find("author").find("name").text if video.find("author") else "YouTube"
                
                mesaj = f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n*{baslik}*\n\n[Hemen İzle]({v_link})"
                telegram_gonder(mesaj)
                print(f"GÖNDERİLDİ: {baslik}")
                
                hafiza_yaz(v_id)
                eski_videolar.append(v_id)
            else:
                print(f"Zaten bildirilmiş: {v_id}")
                    
        except Exception as e:
            print(f"Video kontrol hatası: {e}")

if __name__ == "__main__":
    videolari_kontrol_et()

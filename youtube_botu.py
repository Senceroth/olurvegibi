import requests
from bs4 import BeautifulSoup
import os
import re

# GITHUB SECRETS
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
HAFIZA_DOSYASI = "hafiza_youtube.txt"

# Takip edilecek kanallar
KANALLAR = {
    "GamingBolt": "https://www.youtube.com/@GamingBolt",
    "IGN": "https://www.youtube.com/@IGN",
    "PlayStation": "https://www.youtube.com/@PlayStation"
}

# DOĞRULANMIŞ KESİN KANAL ID'LERİ
# YouTube bazen handle üzerinden ID bulmayı engellediği için yedek liste her zaman hazır.
YEDEK_IDLER = {
    "GamingBolt": "UCf0G79LcyN9oE24yT5p-fVw",
    "IGN": "UC67b8_NfT40X8A3_T3_0gjw",
    "PlayStation": "UCBsbrudhKRrT9zs8iNOEjjw"
}

# Standart tarayıcı başlığı
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

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

def kanal_rss_bul(kanal_adi, kanal_url):
    """Kanal URL'sinden ID bulmaya çalışır, bulamazsa manuel listeden çeker."""
    cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en+FX+419'}
    
    try:
        resp = requests.get(kanal_url, headers=HEADERS, cookies=cookies, timeout=15)
        html = resp.text
        
        # Meta etiketinden ara
        soup = BeautifulSoup(html, "html.parser")
        meta = soup.find("meta", {"itemprop": "channelId"})
        if meta:
            cid = meta['content']
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        
        # Regex ile ara
        match = re.search(r"\"channelId\":\"(UC[^\"]+)\"", html)
        if match:
            cid = match.group(1)
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
            
    except Exception as e:
        print(f"Arama Hatası ({kanal_adi}): {e}")

    # Kazıma başarısız olursa manuel listeyi kullan
    cid = YEDEK_IDLER.get(kanal_adi)
    print(f"Bilgi: {kanal_adi} için yedek ID kullanılıyor.")
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}" if cid else None

def videolari_kontrol_et():
    eski_videolar = hafiza_oku()
    print(f"Hafızadaki eski video sayısı: {len(eski_videolar)}")
    
    for kanal_adi, url in KANALLAR.items():
        print(f"\n--- {kanal_adi} kontrol ediliyor ---")
        rss_url = kanal_rss_bul(kanal_adi, url)
        
        if not rss_url:
            print(f"Hata: RSS bağlantısı oluşturulamadı: {kanal_adi}")
            continue
            
        try:
            # KRİTİK: RSS ÇEKERKEN DE HEADERS KULLANMALIYIZ (404 hatasını bu çözer)
            resp = requests.get(rss_url, headers=HEADERS, timeout=15)
            
            if resp.status_code != 200:
                print(f"Hata: RSS çekilemedi (Kod: {resp.status_code})")
                continue

            soup = BeautifulSoup(resp.content, "xml")
            videolar = soup.find_all("entry")
            
            if not videolar:
                print(f"{kanal_adi} kanalında henüz video bulunamadı.")
                continue
                
            video = videolar[0]
            # ID temizleme işlemi (Ön ekleri kaldır)
            v_id_tag = video.find("yt:videoId") or video.find("id")
            v_id = v_id_tag.text.replace("yt:video:", "").replace("guid", "").strip()
            
            if v_id not in eski_videolar:
                baslik = video.find("title").text.strip()
                v_link = video.find("link")['href'] if video.find("link") else f"https://www.youtube.com/watch?v={v_id}"
                
                mesaj = f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n*{baslik}*\n\n[Hemen İzle]({v_link})"
                telegram_gonder(mesaj)
                print(f"GÖNDERİLDİ: {baslik}")
                
                hafiza_yaz(v_id)
                eski_videolar.append(v_id)
            else:
                print(f"Zaten bildirilmiş: {v_id}")
                    
        except Exception as e:
            print(f"Video kontrol hatası ({kanal_adi}): {e}")

if __name__ == "__main__":
    videolari_kontrol_et()

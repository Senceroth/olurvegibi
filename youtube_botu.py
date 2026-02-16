import requests
from bs4 import BeautifulSoup
import os

# GITHUB SECRETS ÜZERİNDEN GELEN VERİLER
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
    """Daha önce gönderilen video ID'lerini dosyadan okur."""
    if not os.path.exists(HAFIZA_DOSYASI):
        return []
    with open(HAFIZA_DOSYASI, "r") as f:
        return f.read().splitlines()

def hafiza_yaz(veri):
    """Yeni gönderilen video ID'sini dosyaya kaydeder."""
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{veri}\n")

def telegram_gonder(mesaj):
    """Telegram üzerinden bildirim gönderir."""
    if not TOKEN or not CHAT_ID:
        print("Hata: Token veya Chat ID eksik!")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mesaj,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram gönderim hatası: {e}")

def kanal_rss_bul(kanal_url):
    """YouTube kanal URL'sinden gizli RSS beslemesini bulur."""
    base_url = kanal_url.split("/videos")[0]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Meta etiketinden Channel ID bulmaya çalış
        meta = soup.find("meta", {"itemprop": "channelId"})
        if meta:
            channel_id = meta['content']
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        return None
    except Exception as e:
        print(f"RSS bulma hatası ({kanal_url}): {e}")
        return None

def videolari_kontrol_et():
    """Tüm kanalları gezer ve yeni video varsa bildirir."""
    eski_videolar = hafiza_oku()
    print(f"Hafızadaki eski video sayısı: {len(eski_videolar)}")
    
    for kanal_linki in KANALLAR:
        rss_url = kanal_rss_bul(kanal_linki)
        if not rss_url:
            continue
        
        try:
            resp = requests.get(rss_url, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "xml")
                # En son videoyu al (entry etiketi Atom beslemesidir)
                video = soup.find("entry")
                
                if video:
                    video_id = video.find("videoId").text
                    
                    # EĞER BU VİDEO ID'Sİ HAFIZADA YOKSA -> YENİDİR!
                    if video_id not in eski_videolar:
                        baslik = video.find("title").text.strip()
                        link = video.find("link")['href']
                        kanal_adi = video.find("author").find("name").text
                        
                        mesaj = f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n*{baslik}*\n\n[Hemen İzle]({link})"
                        telegram_gonder(mesaj)
                        print(f"Yeni video gönderildi: {baslik}")
                        
                        # Hafızaya kaydet
                        hafiza_yaz(video_id)
                        eski_videolar.append(video_id)
                    else:
                        print(f"Değişiklik yok: {kanal_linki}")
                    
        except Exception as e:
            print(f"Kanal kontrol hatası ({kanal_linki}): {e}")

if __name__ == "__main__":
    videolari_kontrol_et()

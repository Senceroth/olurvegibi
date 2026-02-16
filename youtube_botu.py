import requests
import os

# GITHUB SECRETS ÜZERİNDEN GELEN VERİLER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY") # GitHub Secrets'a eklediğin anahtar
HAFIZA_DOSYASI = "hafiza_youtube.txt"

# Takip edilecek Kanal ID'leri (Scraping gerektirmez, en güvenli yol)
# Not: Kanalların "UC..." ile başlayan benzersiz kimlikleridir.
KANALLAR = {
    "GamingBolt": "UCf0G79LcyN9oE24yT5p-fVw",
    "IGN": "UCrPseYLGpN_WUTREjllH2vA",
    "PlayStation": "UCBsbrudhKRrT9zs8iNOEjjw"
}

def hafiza_oku():
    """Daha önce gönderilen videoların listesini okur."""
    if not os.path.exists(HAFIZA_DOSYASI):
        return set()
    with open(HAFIZA_DOSYASI, "r") as f:
        return set(f.read().splitlines())

def hafiza_yaz(video_id):
    """Yeni gönderilen video ID'sini hafızaya kaydeder."""
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{video_id}\n")

def telegram_gonder(mesaj):
    """Telegram üzerinden bildirim gönderir."""
    if not TOKEN or not CHAT_ID:
        print("HATA: Telegram Token veya Chat ID eksik!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"Telegram Hatası: {r.text}")
    except Exception as e:
        print(f"Telegram bağlantı hatası: {e}")

def son_videoyu_getir(kanal_adi, kanal_id):
    """YouTube Data API v3 kullanarak kanalın en son videosunu çeker."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": kanal_id,
        "part": "snippet",
        "order": "date",
        "maxResults": 1,
        "type": "video"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        # API anahtarı veya kota hatası kontrolü
        if "error" in data:
            print(f"API Hatası ({kanal_adi}): {data['error']['message']}")
            return None
            
        items = data.get("items", [])
        if not items:
            print(f"{kanal_adi}: Video bulunamadı.")
            return None
            
        video_verisi = items[0]
        return {
            "id": video_verisi["id"]["videoId"],
            "baslik": video_verisi["snippet"]["title"],
            "link": f"https://www.youtube.com/watch?v={video_verisi['id']['videoId']}"
        }
    except Exception as e:
        print(f"API isteği sırasında hata oluştu ({kanal_adi}): {e}")
        return None

def videolari_kontrol_et():
    """Tüm kanalları gezer ve yeni video varsa bildirir."""
    if not YOUTUBE_API_KEY:
        print("HATA: YOUTUBE_API_KEY eksik! Lütfen GitHub Secrets'a ekleyin.")
        return

    eski_videolar = hafiza_oku()
    print(f"Hafızadaki toplam video sayısı: {len(eski_videolar)}")
    
    for kanal_adi, kanal_id in KANALLAR.items():
        print(f"\n--- {kanal_adi} kontrol ediliyor ---")
        
        video = son_videoyu_getir(kanal_adi, kanal_id)
        
        if not video:
            continue
            
        # Eğer video ID'si hafızada yoksa yeni videodur
        if video["id"] not in eski_videolar:
            mesaj = (
                f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n"
                f"*{video['baslik']}*\n\n"
                f"[Hemen İzle]({video['link']})"
            )
            telegram_gonder(mesaj)
            print(f"GÖNDERİLDİ: {video['baslik']}")
            
            # Hafızaya kaydet
            hafiza_yaz(video["id"])
            eski_videolar.add(video["id"])
        else:
            print(f"Zaten bildirilmiş: {video['baslik']}")

if __name__ == "__main__":
    videolari_kontrol_et()

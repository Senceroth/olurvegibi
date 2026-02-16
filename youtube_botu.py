import requests
import os

# GITHUB SECRETS ÜZERİNDEN GELEN VERİLER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY") 
HAFIZA_DOSYASI = "hafiza_youtube.txt"

# Takip edilecek Kanallar (UC... ile başlayan Kanal ID'leri)
# Bu ID'ler sabittir ve değişmez, en güvenli yoldur.
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
    """Yeni gönderilen video ID'sini dosyaya kaydeder."""
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

def get_uploads_playlist_id(kanal_id):
    """
    Kanalın 'Yüklenenler' (Uploads) listesinin ID'sini çeker.
    Genelde kanal ID'sinin ikinci harfi 'U' yapılarak bulunur ama 
    resmi yoldan sorgulamak en garantisidir.
    """
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "key": YOUTUBE_API_KEY,
        "id": kanal_id,
        "part": "contentDetails"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except:
        # Hata durumunda standart YouTube kuralını dene (UC... -> UU...)
        return "UU" + kanal_id[2:]

def son_videoyu_getir(kanal_adi, kanal_id):
    """PlaylistItems API kullanarak kanalın en son videosunu %100 doğrulukla çeker."""
    uploads_id = get_uploads_playlist_id(kanal_id)
    
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "key": YOUTUBE_API_KEY,
        "playlistId": uploads_id,
        "part": "snippet",
        "maxResults": 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "error" in data:
            print(f"API Hatası ({kanal_adi}): {data['error']['message']}")
            return None
            
        items = data.get("items", [])
        if not items:
            print(f"{kanal_adi}: Henüz yüklenmiş video bulunamadı.")
            return None
            
        snippet = items[0]["snippet"]
        v_id = snippet["resourceId"]["videoId"]
        return {
            "id": v_id,
            "baslik": snippet["title"],
            "link": f"https://www.youtube.com/watch?v={v_id}"
        }
    except Exception as e:
        print(f"Bağlantı Hatası ({kanal_adi}): {e}")
        return None

def videolari_kontrol_et():
    """Tüm kanalları kontrol eder ve yeni video varsa bildirir."""
    if not YOUTUBE_API_KEY:
        print("HATA: YOUTUBE_API_KEY eksik! GitHub Secrets'a ekleyin.")
        return

    eski_videolar = hafiza_oku()
    print(f"Hafızadaki toplam video sayısı: {len(eski_videolar)}")
    
    for kanal_adi, kanal_id in KANALLAR.items():
        print(f"Kontrol ediliyor: {kanal_adi}")
        
        video = son_videoyu_getir(kanal_adi, kanal_id)
        
        if video:
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
                # Loglarda artık atlanan videoları da görebilirsin
                print(f"Zaten bildirilmiş: {video['baslik'][:50]}...")

if __name__ == "__main__":
    videolari_kontrol_et()

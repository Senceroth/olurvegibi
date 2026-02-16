import requests
import os

# GITHUB SECRETS ÜZERİNDEN GELEN VERİLER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY") 
HAFIZA_DOSYASI = "hafiza_youtube.txt"

# KESİN VE DOĞRULANMIŞ KANAL ID'LERİ (GÜNCELLENDİ)
KANALLAR = {
    "GamingBolt": "UCXa_bzvv7Oo1glaW9FldDhQ",
    "IGN": "UCKy1dAqELo0zrOtPkf0eTMw",
    "PlayStation": "UC-2Y8dQb0S6DtpxNgAKoJKA", # DÜZELTİLDİ: Resmi PlayStation Kanalı
    "GameSpot": "UCbu2SsF-Or3Rsn3NxqODImw"    # YENİ EKLENDİ: GameSpot
}

def hafiza_oku():
    """Daha önce gönderilen videoların listesini okur."""
    if not os.path.exists(HAFIZA_DOSYASI): return set()
    with open(HAFIZA_DOSYASI, "r") as f:
        return set(f.read().splitlines())

def hafiza_yaz(video_id):
    """Yeni gönderilen video ID'sini dosyaya kaydeder."""
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{video_id}\n")

def telegram_gonder(mesaj):
    """Telegram üzerinden bildirim gönderir."""
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

def get_uploads_playlist_id(kanal_id):
    """
    Kanalın 'Yüklenenler' listesinin gerçek ID'sini API'den sorar.
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
        
        # Eğer ID yanlışsa API 'items' dizisini boş döndürür
        if "items" not in data or len(data["items"]) == 0:
            print(f"Hata: Bu Kanal ID ({kanal_id}) geçersiz!")
            return None
            
        return data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except Exception as e:
        print(f"Playlist ID Bulma Hatası: {e}")
        return None

def son_videoyu_getir(kanal_adi, kanal_id):
    # Önce doğru playlist ID'sini buluyoruz
    uploads_id = get_uploads_playlist_id(kanal_id)
    
    if not uploads_id:
        print(f"Hata: {kanal_adi} için liste bulunamadı.")
        return None
    
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
            return None
            
        snippet = items[0]["snippet"]
        v_id = snippet["resourceId"]["videoId"]
        return {
            "id": v_id,
            "baslik": snippet["title"],
            "link": f"https://www.youtube.com/watch?v={v_id}"
        }
    except Exception as e:
        print(f"Hata ({kanal_adi}): {e}")
        return None

def videolari_kontrol_et():
    if not YOUTUBE_API_KEY:
        print("API Key Eksik!")
        return

    eski_videolar = hafiza_oku()
    
    for kanal_adi, kanal_id in KANALLAR.items():
        print(f"Kontrol ediliyor: {kanal_adi}...")
        video = son_videoyu_getir(kanal_adi, kanal_id)
        
        if video and video["id"] not in eski_videolar:
            mesaj = f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n*{video['baslik']}*\n\n[İzle]({video['link']})"
            telegram_gonder(mesaj)
            print(f"--> GÖNDERİLDİ: {video['baslik']}")
            
            hafiza_yaz(video["id"])
            eski_videolar.add(video["id"])
        elif video:
            print(f"Zaten kayıtlı: {video['baslik'][:40]}...")

if __name__ == "__main__":
    videolari_kontrol_et()

import requests
import os

# GITHUB SECRETS
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY") 
HAFIZA_DOSYASI = "hafiza_youtube.txt"

# Takip edilecek Kanallar (ID'leri doğrulandı)
KANALLAR = {
    "GamingBolt": "UCf0G79LcyN9oE24yT5p-fVw",
    "IGN": "UCrPseYLGpN_WUTREjllH2vA",
    "PlayStation": "UCBsbrudhKRrT9zs8iNOEjjw"
}

def hafiza_oku():
    if not os.path.exists(HAFIZA_DOSYASI):
        return set()
    with open(HAFIZA_DOSYASI, "r") as f:
        return set(f.read().splitlines())

def hafiza_yaz(video_id):
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{video_id}\n")

def telegram_gonder(mesaj):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

def son_videoyu_getir(kanal_adi, kanal_id):
    """
    Search yerine PlaylistItems kullanarak kanalın yüklenenler 
    listesindeki en son videoyu %100 doğrulukla çeker.
    """
    # Kanal ID'sinin 2. harfini 'U' yaparak 'Uploads' listesine ulaşılır
    uploads_playlist_id = "UU" + kanal_id[2:]
    
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "key": YOUTUBE_API_KEY,
        "playlistId": uploads_playlist_id,
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
            print(f"{kanal_adi}: Liste boş dönüyor.")
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
    if not YOUTUBE_API_KEY:
        print("YOUTUBE_API_KEY eksik!")
        return

    eski_videolar = hafiza_oku()
    print(f"Hafızadaki video sayısı: {len(eski_videolar)}")
    
    for kanal_adi, kanal_id in KANALLAR.items():
        print(f"Kontrol ediliyor: {kanal_adi}")
        video = son_videoyu_getir(kanal_adi, kanal_id)
        
        if video and video["id"] not in eski_videolar:
            mesaj = (
                f"▶️ *YENİ VİDEO! ({kanal_adi})*\n\n"
                f"*{video['baslik']}*\n\n"
                f"[Hemen İzle]({video['link']})"
            )
            telegram_gonder(mesaj)
            print(f"GÖNDERİLDİ: {video['baslik']}")
            hafiza_yaz(video["id"])
            eski_videolar.add(video["id"])
        elif video:
            print(f"Zaten kayıtlı: {video['baslik']}")

if __name__ == "__main__":
    videolari_kontrol_et()

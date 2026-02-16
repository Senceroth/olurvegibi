import requests
import os

# GITHUB SECRETS ÜZERİNDEN GELEN VERİLER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
HAFIZA_DOSYASI = "hafiza_gamerpower.txt"

def hafiza_oku():
    """Daha önce gönderilen fırsat ID'lerini dosyadan okur."""
    if not os.path.exists(HAFIZA_DOSYASI):
        return []
    with open(HAFIZA_DOSYASI, "r") as f:
        return f.read().splitlines()

def hafiza_yaz(yeni_id):
    """Yeni fırsat ID'sini dosyaya kaydeder."""
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{yeni_id}\n")

def telegram_gonder(mesaj, resim_url=None):
    """Telegram üzerinden bildirim gönderir (Resimli veya resimsiz)."""
    if not TOKEN or not CHAT_ID:
        print("Hata: Token veya Chat ID eksik!")
        return
    try:
        if resim_url:
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            payload = {
                "chat_id": CHAT_ID,
                "photo": resim_url,
                "caption": mesaj,
                "parse_mode": "Markdown"
            }
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": CHAT_ID,
                "text": mesaj,
                "parse_mode": "Markdown"
            }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def firsatlari_tara():
    """GamerPower API üzerinden PC fırsatlarını kontrol eder."""
    print("GamerPower taranıyor (Hafızalı Mod)...")
    url = "https://www.gamerpower.com/api/giveaways"
    params = {"platform": "pc", "type": "game", "sort-by": "newest"}
    
    eski_idler = hafiza_oku()
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Sadece en yeni 5 fırsata bakmak yeterli (Gereksiz trafik yaratmayalım)
            for item in data[:5]:
                if item.get("status") == "Active":
                    oyun_id = str(item.get("id"))
                    
                    # EĞER BU ID HAFIZADA YOKSA -> YENİ FIRSAT!
                    if oyun_id not in eski_idler:
                        baslik = item.get("title")
                        platformlar = item.get("platforms")
                        deger = item.get("worth")
                        link = item.get("open_giveaway_url")
                        resim = item.get("thumbnail")
                        
                        mesaj = (
                            f"🚨 *YENİ BEDAVA OYUN!* 🚨\n\n"
                            f"🎮 *{baslik}*\n"
                            f"🏢 Platform: {platformlar}\n"
                            f"💰 Değeri: {deger}\n\n"
                            f"[👉 Hemen Kap]({link})"
                        )
                        
                        telegram_gonder(mesaj, resim)
                        print(f"Yeni fırsat gönderildi: {baslik}")
                        
                        # Hafızaya ekle
                        hafiza_yaz(oyun_id)
                        eski_idler.append(oyun_id)
                    else:
                        print(f"Eski fırsat, atlanıyor: {item.get('title')}")
        else:
            print(f"API Hatası: {response.status_code}")
            
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")

if __name__ == "__main__":
    firsatlari_tara()

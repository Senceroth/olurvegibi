import requests
import os
from datetime import datetime, timedelta

# GITHUB'DAN GELECEK ŞİFRELER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")

def telegram_gonder(mesaj, resim_url=None):
    if not TOKEN or not CHAT_ID:
        print("Token veya Chat ID yok!")
        return
    try:
        if resim_url:
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            payload = {"chat_id": CHAT_ID, "photo": resim_url, "caption": mesaj, "parse_mode": "Markdown"}
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Hata: {e}")

def firsatlari_tara():
    print("GamerPower taranıyor...")
    url = "https://www.gamerpower.com/api/giveaways"
    params = {"platform": "pc", "type": "game", "sort-by": "newest"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # ŞU ANKİ ZAMAN
            simdi = datetime.utcnow()
            
            for item in data:
                # Sadece AKTİF olanlar
                if item.get("status") == "Active":
                    # YAYINLANMA TARİHİNE BAK
                    yayin_tarihi_str = item.get("published_date")
                    yayin_tarihi = datetime.strptime(yayin_tarihi_str, "%Y-%m-%d %H:%M:%S")
                    
                    # EĞER SON 45 DAKİKA İÇİNDE YAYINLANDIYSA BİLDİR
                    fark = simdi - yayin_tarihi
                    if fark < timedelta(minutes=45):
                        mesaj = (
                            f"🚨 *YENİ FIRSAT YAKALANDI!* 🚨\n\n"
                            f"🎮 *{item.get('title')}*\n"
                            f"🏢 {item.get('platforms')}\n"
                            f"💰 Değeri: {item.get('worth')}\n\n"
                            f"[👉 Hemen Kap]({item.get('open_giveaway_url')})"
                        )
                        telegram_gonder(mesaj, item.get("thumbnail"))
                        print(f"Bildirim atıldı: {item.get('title')}")
        else:
            print("API hatası.")
    except Exception as e:
        print(f"Bağlantı hatası: {e}")

if __name__ == "__main__":
    firsatlari_tara()
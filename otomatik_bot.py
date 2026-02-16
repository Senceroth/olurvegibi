import requests
import os

# GITHUB'DAN GELECEK ŞİFRELER
TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
HAFIZA_DOSYASI = "hafiza_gamerpower.txt"

def hafiza_oku():
    if not os.path.exists(HAFIZA_DOSYASI): return []
    with open(HAFIZA_DOSYASI, "r") as f:
        return f.read().splitlines()

def hafiza_yaz(yeni_id):
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{yeni_id}\n")

def telegram_gonder(mesaj, resim_url=None):
    if not TOKEN or not CHAT_ID: return
    try:
        if resim_url:
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            payload = {"chat_id": CHAT_ID, "photo": resim_url, "caption": mesaj, "parse_mode": "Markdown"}
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def firsatlari_tara():
    print("GamerPower taranıyor (Hafızalı Mod)...")
    url = "https://www.gamerpower.com/api/giveaways"
    params = {"platform": "pc", "type": "game", "sort-by": "newest"}
    
    # Eskiden gönderdiklerimizi hafızadan okuyoruz
    eski_idler = hafiza_oku()
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Sadece en yeni 5 tanesini kontrol etsek yeterli
            # (Çok eskilere gitmeye gerek yok, zaten hafızada yoksa yenidir)
            for item in data[:5]:
                if item.get("status") == "Active":
                    oyun_id = str(item.get("id"))
                    
                    # EĞER BU ID DAHA ÖNCE KAYDEDİLMEMİŞSE -> YENİDİR!
                    if oyun_id not in eski_idler:
                        mesaj = (
                            f"🚨 *YENİ FIRSAT!* 🚨\n\n"
                            f"🎮 *{item.get('title')}*\n"
                            f"🏢 {item.get('platforms')}\n"
                            f"💰 Değeri: {item.get('worth')}\n\n"
                            f"[👉 Hemen Kap]({item.get('open_giveaway_url')})"
                        )
                        telegram_gonder(mesaj, item.get("thumbnail"))
                        print(f"YENİ: {item.get('title')}")
                        
                        # Hafızaya ekle ve listeyi güncelle
                        hafiza_yaz(oyun_id)
                        eski_idler.append(oyun_id)
        else:
            print("API hatası.")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    firsatlari_tara()

import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("TG_CHAT_ID")
HAFIZA_DOSYASI = "hafiza_eurogamer.txt"

def hafiza_oku():
    if not os.path.exists(HAFIZA_DOSYASI): return []
    with open(HAFIZA_DOSYASI, "r") as f:
        return f.read().splitlines()

def hafiza_yaz(veri):
    with open(HAFIZA_DOSYASI, "a") as f:
        f.write(f"{veri}\n")

def telegram_gonder(mesaj):
    if not TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def haberleri_kontrol_et():
    url = "https://www.eurogamer.net/feed/news"
    # Daha gerçekçi tarayıcı kimliği (Bot korumasını aşmak için)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    eski_haberler = hafiza_oku()
    print(f"Hafızadaki haber sayısı: {len(eski_haberler)}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Site Durumu: {response.status_code}")
        
        if response.status_code == 200:
            # XML verisini okuyoruz
            soup = BeautifulSoup(response.content, "xml")
            haberler = soup.find_all("entry")
            print(f"Bulunan toplam haber: {len(haberler)}")
            
            # Sadece en güncel 5 haberi kontrol et (Yeterli olacaktır)
            for haber in haberler[:5]:
                try:
                    haberi_id = haber.find("id").text
                    baslik = haber.find("title").text
                    
                    # Eğer bu ID hafızada yoksa -> YENİ HABER
                    if haberi_id not in eski_haberler:
                        link = haber.find("link")['href']
                        mesaj = f"📰 *YENİ HABER (Eurogamer)*\n\n*{baslik}*\n\n[Oku]({link})"
                        
                        telegram_gonder(mesaj)
                        print(f"--> GÖNDERİLDİ: {baslik}")
                        
                        # Hafızaya kaydet
                        hafiza_yaz(haberi_id)
                        eski_haberler.append(haberi_id)
                    else:
                        print(f"--- Eski haber: {baslik}")
                        
                except Exception as e:
                    print(f"Haber işleme hatası: {e}")
        else:
            print("Siteye girilemedi (Engellendi veya hata).")
            
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")

if __name__ == "__main__":
    haberleri_kontrol_et()

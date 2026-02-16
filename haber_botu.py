import requests
from bs4 import BeautifulSoup
import os

# GITHUB'DAN GELECEK ŞİFRELER
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
    # Eurogamer'ın resmi RSS beslemesi
    url = "https://www.eurogamer.net/feed/news"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Hafızadaki eski haber ID'lerini oku
    eski_haberler = hafiza_oku()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # XML verisini okuyoruz
            soup = BeautifulSoup(response.content, "xml")
            haberler = soup.find_all("entry")
            
            # Sadece en güncel 5 haberi kontrol etsek yeterli
            # (Çok eskilere gitmeye gerek yok, zaten hafızada yoksa yenidir)
            for haber in haberler[:5]:
                try:
                    # Her haberin kendine özel bir ID'si vardır
                    haberi_id = haber.find("id").text
                    
                    # EĞER BU ID HAFIZADA YOKSA -> YENİDİR!
                    if haberi_id not in eski_haberler:
                        baslik = haber.find("title").text
                        link = haber.find("link")['href']
                        
                        mesaj = f"📰 *HABER (Eurogamer)*\n\n*{baslik}*\n\n[Oku]({link})"
                        telegram_gonder(mesaj)
                        print(f"Yeni haber gönderildi: {baslik}")
                        
                        # Hafızaya kaydet
                        hafiza_yaz(haberi_id)
                        eski_haberler.append(haberi_id)
                except:
                    continue # ID veya başlık bulunamazsa o haberi atla

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    haberleri_kontrol_et()

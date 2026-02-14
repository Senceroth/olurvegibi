import streamlit as st
from bs4 import BeautifulSoup
import time
from datetime import datetime
import undetected_chromedriver as uc
import requests 

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SteamDB Bedava Oyun Takip", page_icon="🎁", layout="wide")

# --- TELEGRAM FONKSİYONU ---
def telegram_gonder(token, chat_id, mesaj):
    if not token or not chat_id: return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
        return True
    except:
        return False

# --- TARAYICI İLE VERİ ÇEKME ---
def tarayici_ile_cek():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless") # <-- BU SATIR ÇOK ÖNEMLİ (Sunucuda ekran olmadığı için açtık)

    driver = None
    try:
        # Chrome'u başlat (Sürüm kilidini kaldırdık, sunucu ne varsa onu kullansın)
        driver = uc.Chrome(options=options, use_subprocess=True) 
        
        driver.get("https://steamdb.info/upcoming/free/")
        
        # Cloudflare kontrolünü geçmesi için bekleme süresi
        time.sleep(10) 
        
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        oyunlar = []
        eklenen_idler = set() # Aynı oyunu iki kere eklememek için

        # --- YÖNTEM 1: KART GÖRÜNÜMÜ (GRID) TARAMASI ---
        tum_linkler = soup.find_all("a", href=True)
        
        for link in tum_linkler:
            href = link['href']
            
            # Sadece oyun (app) veya paket (sub) linklerine bak
            if not ("/app/" in href or "/sub/" in href):
                continue
            
            # Bu linkin içinde bulunduğu ana kutuyu (parent) bulmaya çalışalım
            kutu = link.find_parent("div")
            if not kutu: continue
            
            # Kutunun içindeki tüm yazıları al
            kutu_metni = kutu.get_text(" ", strip=True)
            
            # Eğer kutuda "Free" kelimesi geçmiyorsa bu bir menü linki olabilir, atla
            if "Free" not in kutu_metni and "Keep" not in kutu_metni:
                continue

            # ID'yi al
            parts = href.strip("/").split("/")
            app_id = parts[-1] if len(parts) > 0 else "unknown"
            
            # Zaten eklediysek atla
            if app_id in eklenen_idler:
                continue

            # Oyun Adını Bulma
            oyun_adi = link.get_text(strip=True)
            if not oyun_adi or len(oyun_adi) < 2:
                baslik_tag = kutu.find("b") or kutu.find("h3") or kutu.find("span", class_="name")
                if baslik_tag:
                    oyun_adi = baslik_tag.get_text(strip=True)
                else:
                    oyun_adi = "Oyun Başlığı Bulunamadı"

            # Türü Belirle
            tur = "Bilinmiyor"
            if "Free to Keep" in kutu_metni:
                tur = "🎁 Sonsuza Kadar Senin (Keep)"
            elif "Play For Free" in kutu_metni:
                tur = "⏳ Hafta Sonu Denemesi (Play)"
            
            steam_link = f"https://store.steampowered.com/app/{app_id}/" if "app" in href else f"https://store.steampowered.com/sub/{app_id}/"
            
            # Listeye Ekle
            oyunlar.append({
                "ad": oyun_adi,
                "link": steam_link,
                "tur": tur,
                "zaman": "Detaylar Sitede", 
                "id": app_id
            })
            eklenen_idler.add(app_id)

        # Eğer Kartlardan bir şey çıkmadıysa Klasik Tabloyu dene (Yedek)
        if not oyunlar:
            satirlar = soup.select("tr.app") 
            for satir in satirlar:
                pass
            
        return oyunlar

    except Exception as e:
        return f"ERROR: {str(e)}"
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# --- ARAYÜZ ---
st.title("🎁 SteamDB Otomatik Ajanı")
st.markdown("Tarayıcıyı açar, 'Free to Keep' ve 'Play For Free' oyunlarını akıllıca bulur.")

default_token = "8160497699:AAG2hCZIa_yueqTf3waAUV6r2lXTojUut0A"
default_chat_id = "8355841229"

if "bedava_oyunlar_listesi" not in st.session_state:
    st.session_state.bedava_oyunlar_listesi = []

with st.sidebar:
    st.header("⚙️ Ayarlar")
    tg_token = st.text_input("Bot Token", value=default_token, type="password")
    tg_chat_id = st.text_input("Chat ID", value=default_chat_id)
    st.success("Bot sunucu modunda çalışıyor (Headless).")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Liste Durumu")
    
    if st.button("Listeyi Tarayıcıyla Çek"):
        with st.spinner("Ajan gönderildi... (15-20 saniye sürebilir)"):
            sonuc = tarayici_ile_cek()
            
            if isinstance(sonuc, str) and sonuc.startswith("ERROR"):
                st.error(f"Hata: {sonuc}")
            elif sonuc:
                st.session_state.bedava_oyunlar_listesi = sonuc
                st.success(f"✅ Başarılı! {len(sonuc)} oyun bulundu.")
            else:
                st.warning("Siteye girildi ama oyun bulunamadı.")

    if st.session_state.bedava_oyunlar_listesi:
        for oyun in st.session_state.bedava_oyunlar_listesi:
            with st.expander(f"🎮 {oyun['ad']}"):
                st.write(f"📌 **Tür:** {oyun['tur']}")
                st.link_button("Steam'de Gör", oyun['link'])

with col2:
    st.subheader("📡 Otomatik Takip")
    dakika = st.slider("Dakika", 30, 240, 60)
    
    if st.button("Takibi Başlat 🚀"):
        st.success("Otomatik Ajan Başlatıldı! Arka planda çalışıyor.")
        telegram_gonder(tg_token, tg_chat_id, "🎁 *Otomatik Takip Başladı!*")
        
        ilk_veri = tarayici_ile_cek()
        if isinstance(ilk_veri, list):
            st.session_state.kayitli_idier = [oyun['id'] for oyun in ilk_veri]
        else:
            st.session_state.kayitli_idier = []

        log_kutusu = st.empty()
        
        while True:
            time.sleep(dakika * 60)
            tarih = datetime.now().strftime('%H:%M')
            
            yeni_liste = tarayici_ile_cek()
            
            if isinstance(yeni_liste, list) and yeni_liste:
                yeni_bulunanlar = 0
                for oyun in yeni_liste:
                    if oyun['id'] not in st.session_state.kayitli_idier:
                        icon = "🎁" if "Keep" in oyun['tur'] else "⏳"
                        mesaj = f"{icon} *YENİ BEDAVA OYUN!*\n\n🎮 *{oyun['ad']}*\n📌 {oyun['tur']}\n[Steam Linki]({oyun['link']})"
                        telegram_gonder(tg_token, tg_chat_id, mesaj)
                        st.session_state.kayitli_idier.append(oyun['id'])
                        yeni_bulunanlar += 1
                
                if yeni_bulunanlar > 0:
                    log_kutusu.success(f"[{tarih}] ✅ {yeni_bulunanlar} yeni oyun!")
                else:
                    log_kutusu.info(f"[{tarih}] 💤 Yeni oyun yok.")
            elif isinstance(yeni_liste, str):
                log_kutusu.error(f"[{tarih}] Hata: {yeni_liste[:50]}...")
            else:
                log_kutusu.warning(f"[{tarih}] Liste boş.")

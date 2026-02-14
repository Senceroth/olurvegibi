import streamlit as st
from bs4 import BeautifulSoup
import time
from datetime import datetime
import undetected_chromedriver as uc
import requests 
import os

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
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = None
    ekran_goruntusu = None
    sayfa_basligi = ""

    try:
        # Sürüm 144'e sabitli (Hata alırsan burayı silip boş bırakmayı dene)
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=144) 
        
        driver.get("https://steamdb.info/upcoming/free/")
        
        # Bekleme süresini biraz arttırdık
        time.sleep(15) 
        
        # Sayfa başlığını al (Debug için)
        sayfa_basligi = driver.title
        
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        oyunlar = []
        eklenen_idler = set() 

        # Grid Taraması
        tum_linkler = soup.find_all("a", href=True)
        for link in tum_linkler:
            href = link['href']
            if not ("/app/" in href or "/sub/" in href): continue
            
            kutu = link.find_parent("div")
            if not kutu: continue
            
            kutu_metni = kutu.get_text(" ", strip=True)
            if "Free" not in kutu_metni and "Keep" not in kutu_metni: continue

            parts = href.strip("/").split("/")
            app_id = parts[-1] if len(parts) > 0 else "unknown"
            
            if app_id in eklenen_idler: continue

            oyun_adi = link.get_text(strip=True)
            if not oyun_adi or len(oyun_adi) < 2:
                baslik_tag = kutu.find("b") or kutu.find("h3") or kutu.find("span", class_="name")
                oyun_adi = baslik_tag.get_text(strip=True) if baslik_tag else "İsimsiz Oyun"

            tur = "Bilinmiyor"
            if "Free to Keep" in kutu_metni: tur = "🎁 Sonsuza Kadar Senin (Keep)"
            elif "Play For Free" in kutu_metni: tur = "⏳ Hafta Sonu Denemesi (Play)"
            
            steam_link = f"https://store.steampowered.com/app/{app_id}/" if "app" in href else f"https://store.steampowered.com/sub/{app_id}/"
            
            oyunlar.append({"ad": oyun_adi, "link": steam_link, "tur": tur, "zaman": "Sitede", "id": app_id})
            eklenen_idler.add(app_id)

        # Eğer oyun bulamazsa FOTOĞRAF ÇEK
        if not oyunlar:
            driver.save_screenshot("hata_resmi.png")
            ekran_goruntusu = "hata_resmi.png"
            
        return oyunlar, ekran_goruntusu, sayfa_basligi

    except Exception as e:
        return str(e), None, "Hata"
    finally:
        if driver:
            try: driver.quit()
            except: pass

# --- ARAYÜZ ---
st.title("🎁 SteamDB Ajanı (Kamera Modu)")

default_token = "8160497699:AAG2hCZIa_yueqTf3waAUV6r2lXTojUut0A"
default_chat_id = "8355841229"

if "bedava_oyunlar_listesi" not in st.session_state:
    st.session_state.bedava_oyunlar_listesi = []

with st.sidebar:
    st.header("⚙️ Ayarlar")
    tg_token = st.text_input("Bot Token", value=default_token, type="password")
    tg_chat_id = st.text_input("Chat ID", value=default_chat_id)
    st.info("Eğer liste boş gelirse, bot ne gördüğünü fotoğraflayıp sana gösterecek.")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Liste Durumu")
    
    if st.button("Listeyi Tarayıcıyla Çek"):
        with st.spinner("Ajan siteye giriyor... (Fotoğraf çekiliyor olabilir)"):
            sonuc, resim, baslik = tarayici_ile_cek()
            
            if isinstance(sonuc, str): # Hata mesajı döndüyse
                st.error(f"Hata: {sonuc}")
            
            elif sonuc: # Oyun bulunduysa
                st.session_state.bedava_oyunlar_listesi = sonuc
                st.success(f"✅ Başarılı! {len(sonuc)} oyun bulundu.")
            
            else: # Oyun yoksa
                st.warning(f"Oyun bulunamadı. Botun gördüğü sayfa başlığı: **{baslik}**")
                if resim:
                    st.error("Botun gördüğü ekran aşağıdadır (Cloudflare Engeli Olabilir):")
                    st.image(resim, caption="Botun Gözünden SteamDB", use_column_width=True)

    if st.session_state.bedava_oyunlar_listesi:
        for oyun in st.session_state.bedava_oyunlar_listesi:
            with st.expander(f"🎮 {oyun['ad']}"):
                st.write(f"📌 **Tür:** {oyun['tur']}")
                st.link_button("Steam'de Gör", oyun['link'])

with col2:
    st.subheader("📡 Otomatik Takip")
    dakika = st.slider("Dakika", 30, 240, 60)
    
    if st.button("Takibi Başlat 🚀"):
        st.success("Takip Başladı!")
        telegram_gonder(tg_token, tg_chat_id, "🎁 *SteamDB Takibi Başladı!*")
        
        # İlk kontrol
        veriler, _, _ = tarayici_ile_cek()
        if isinstance(veriler, list):
            st.session_state.kayitli_idier = [oyun['id'] for oyun in veriler]
        else:
            st.session_state.kayitli_idier = []

        log_kutusu = st.empty()
        
        while True:
            time.sleep(dakika * 60)
            tarih = datetime.now().strftime('%H:%M')
            
            yeni_liste, resim_path, _ = tarayici_ile_cek()
            
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
            else:
                log_kutusu.warning(f"[{tarih}] Veri çekilemedi. (Muhtemelen Cloudflare)")

import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# Sayfa ayarları
st.set_page_config(page_title="Eurogamer Haber Takip", page_icon="🎮", layout="wide")

# --- Telegram Fonksiyonu ---
def telegram_gonder(token, chat_id, mesaj):
    """Telegram üzerinden mesaj gönderir. Hata varsa sebebini söyler."""
    if not token or not chat_id:
        return False, "Token veya Chat ID eksik."
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mesaj,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True, "Başarılı"
        else:
            hata_detayi = response.json().get("description", "Bilinmeyen Hata")
            return False, f"Hata ({response.status_code}): {hata_detayi}"
            
    except Exception as e:
        return False, f"Bağlantı Hatası: {str(e)}"

# --- Haber Çekme Fonksiyonları ---

def icerik_detayini_cek(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            paragraflar = soup.find_all("p")
            metin = ""
            for p in paragraflar:
                text = p.get_text(strip=True)
                if len(text) > 50 and "cookie" not in text.lower():
                    metin += text + "\n\n"
            return metin if metin else "İçerik metni bulunamadı."
        else:
            return "İçerik çekilemedi."
    except Exception:
        return "Bağlantı hatası."

def haberleri_getir(detayli_tarama=False):
    url = "https://www.eurogamer.net/latest"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            bulunan_haberler = []
            seen_links = set()

            tum_linkler = soup.find_all("a", href=True)
            progress_bar = st.progress(0) if detayli_tarama else None
            sayac = 0
            
            for link_tag in tum_linkler:
                baslik = link_tag.get_text(strip=True)
                href = link_tag['href']

                if len(baslik) < 25: continue
                if any(x in baslik.lower() for x in ["log in", "sign up", "register", "subscribe", "cookie", "policy"]): continue
                
                full_link = href
                if href.startswith("/"):
                    full_link = "https://www.eurogamer.net" + href
                
                if full_link in seen_links: continue

                haber = {"baslik": baslik, "link": full_link, "detay": ""}
                
                if detayli_tarama and sayac < 10: 
                    time.sleep(0.5) 
                    haber["detay"] = icerik_detayini_cek(full_link)
                
                seen_links.add(full_link)
                bulunan_haberler.append(haber)
                sayac += 1
                
                if detayli_tarama and progress_bar:
                     progress_bar.progress(min(sayac * 10, 100))

                if sayac >= 20: 
                    break
            
            if progress_bar: progress_bar.empty()
            return bulunan_haberler
        else:
            return []
    except Exception as e:
        return []

def txt_olustur(haberler):
    txt_data = f"EUROGAMER RAPORU - {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
    txt_data += "="*30 + "\n\n"
    for haber in haberler:
        txt_data += f"BAŞLIK: {haber['baslik']}\n"
        txt_data += f"LİNK: {haber['link']}\n"
        if haber['detay']:
            txt_data += f"İÇERİK:\n{haber['detay'][:500]}...\n"
        txt_data += "-"*30 + "\n"
    return txt_data

# --- ARAYÜZ ---

st.title("🎮 Eurogamer Haber Merkezi")

# Session State Tanımlamaları
if "takip_modu" not in st.session_state:
    st.session_state.takip_modu = False
if "son_haber_basliklari" not in st.session_state:
    st.session_state.son_haber_basliklari = []
if "log_gecmisi" not in st.session_state:
    st.session_state.log_gecmisi = []

with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    detayli_mod = st.checkbox("İçerikleri de Oku (Yavaşlatır)", value=False)
    
    st.divider()
    st.subheader("📢 Telegram Bildirim")
    
    # Kullanıcı bilgileri (Otomatik Dolu)
    default_token = "8160497699:AAG2hCZIa_yueqTf3waAUV6r2lXTojUut0A"
    default_chat_id = "8355841229"
    
    tg_token = st.text_input("Bot Token", value=default_token, type="password", help="BotFather'dan aldığın kod")
    tg_chat_id = st.text_input("Chat ID", value=default_chat_id, help="userinfobot'tan aldığın numara")
    
    if tg_token and tg_chat_id:
        if st.button("Test Mesajı Gönder"):
            basarili, sonuc_mesaji = telegram_gonder(tg_token, tg_chat_id, "🔔 *Test:* Eurogamer botu başarıyla bağlandı!")
            if basarili:
                st.success("✅ Mesaj gönderildi! Telegram'ı kontrol et.")
            else:
                st.error(f"❌ Gönderilemedi! Sebep: {sonuc_mesaji}")
    
    st.divider()
    
    # Manuel Yenileme
    if st.button("Haberleri Çek / Yenile", type="primary"):
        with st.spinner('Haberler taranıyor...'):
            st.session_state["haberler"] = haberleri_getir(detayli_mod)
            if st.session_state["haberler"]:
                st.session_state.son_haber_basliklari = [h["baslik"] for h in st.session_state["haberler"]]

    # İndirme Butonu
    if "haberler" in st.session_state and st.session_state["haberler"]:
        st.write("📥 **Raporlama**")
        txt_icerik = txt_olustur(st.session_state["haberler"])
        st.download_button("TXT İndir", data=txt_icerik, file_name="eurogamer_haberler.txt", mime="text/plain")

# --- ANA EKRAN VE TAKİP MODU ---

tab1, tab2 = st.tabs(["📋 Haber Listesi", "📡 Otomatik Takip Modu"])

with tab1:
    if "haberler" in st.session_state and st.session_state["haberler"]:
        haberler = st.session_state["haberler"]
        st.success(f"Son Güncelleme: {datetime.now().strftime('%H:%M')} - {len(haberler)} haber mevcut.")
        
        for haber in haberler:
            with st.expander(f"📰 {haber['baslik']}"):
                if haber['detay']:
                    st.markdown(haber['detay'])
                else:
                    st.info("Detay çekilmedi.")
                st.link_button("Habere Git 🔗", haber['link'])
    else:
        st.info("Haberleri görmek için soldan 'Haberleri Çek' butonuna bas.")

with tab2:
    st.markdown("### 📡 Canlı Takip Sistemi")
    st.write("Bu modda uygulama belirlediğin sürede bir siteyi kontrol eder.")
    
    dakika = st.slider("Kaç dakikada bir kontrol edilsin?", 1, 60, 10)
    
    if st.button("Takibi Başlat 🚀"):
        if not tg_token or not tg_chat_id:
            st.error("Lütfen önce sol menüden Telegram Token ve Chat ID gir.")
        else:
            basarili, msj = telegram_gonder(tg_token, tg_chat_id, f"🚀 *Takip Başlatıldı!*\nEurogamer botu {dakika} dakikada bir kontrol edecek.")
            
            if not basarili:
                st.error(f"❌ Başlatılamadı! Telegram Hatası: {msj}")
            else:
                st.success(f"Takip başladı! Her {dakika} dakikada bir kontrol edilecek.")
                
                # Log alanı ve durum göstergeleri
                durum_kutusu = st.empty()
                log_kutusu = st.empty()
                dongu_sayaci = 1
                
                while True:
                    # Şu anki zaman
                    zaman_damgasi = datetime.now().strftime('%H:%M:%S')
                    
                    # Haberleri çek (Hızlı modda)
                    yeni_haberler = haberleri_getir(detayli_tarama=False)
                    
                    log_mesaji = ""
                    
                    if yeni_haberler:
                        yeni_tespitler = []
                        for haber in yeni_haberler:
                            # MANTIK: Eğer başlık hafızada YOKSA yenidir
                            if haber["baslik"] not in st.session_state.son_haber_basliklari:
                                yeni_tespitler.append(haber)
                        
                        if yeni_tespitler:
                            for yeni in yeni_tespitler:
                                mesaj = f"🚨 *YENİ HABER DÜŞTÜ!* 🚨\n\n*{yeni['baslik']}*\n\n[Habere Git]({yeni['link']})"
                                telegram_gonder(tg_token, tg_chat_id, mesaj)
                                # Hafızaya ekle ki bir daha göndermesin
                                st.session_state.son_haber_basliklari.append(yeni["baslik"])
                            
                            log_mesaji = f"[{zaman_damgasi}] ✅ {len(yeni_tespitler)} YENİ HABER BULUNDU VE GÖNDERİLDİ!"
                            durum_kutusu.success(log_mesaji)
                        else:
                            log_mesaji = f"[{zaman_damgasi}] 💤 Kontrol edildi, yeni haber yok."
                            durum_kutusu.info(log_mesaji)
                    else:
                        log_mesaji = f"[{zaman_damgasi}] ⚠️ Siteye bağlanılamadı veya haber çekilemedi."
                        durum_kutusu.warning(log_mesaji)
                    
                    # Log geçmişine ekle (En yenisi en üste)
                    st.session_state.log_gecmisi.insert(0, log_mesaji)
                    # Log geçmişini çok şişirmemek için son 20 kaydı tutalım
                    st.session_state.log_gecmisi = st.session_state.log_gecmisi[:20]
                    
                    # Log kutusunu güncelle
                    log_text = "İŞLEM GEÇMİŞİ:\n" + "\n".join(st.session_state.log_gecmisi)
                    log_kutusu.code(log_text)
                    
                    dongu_sayaci += 1
                    time.sleep(dakika * 60)
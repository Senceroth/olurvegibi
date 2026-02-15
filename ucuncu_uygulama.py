import streamlit as st
import requests
import time
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Bedava Oyun Avcısı (Tüm Platformlar)", page_icon="🎁", layout="wide")

# --- TELEGRAM FONKSİYONU ---
def telegram_gonder(token, chat_id, mesaj, resim_url=None):
    if not token or not chat_id: return False
    
    try:
        if resim_url:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {
                "chat_id": chat_id,
                "photo": resim_url,
                "caption": mesaj,
                "parse_mode": "Markdown"
            }
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": mesaj,
                "parse_mode": "Markdown"
            }
            
        requests.post(url, json=payload, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram Hatası: {e}")
        return False

# --- GAMERPOWER API İLE VERİ ÇEKME ---
def firsatlari_cek():
    url = "https://www.gamerpower.com/api/giveaways"
    
    # ARTIK KAPSAMI GENİŞLETTİK: Sadece Steam değil, PC'deki tüm oyunlar.
    # platform="pc" -> Steam, Epic Games, Ubisoft, GOG, Itch.io vb. hepsini içerir.
    params = {
        "platform": "pc", 
        "type": "game",       
        "sort-by": "newest"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            oyunlar = []
            for item in data:
                if item.get("status") == "Active":
                    oyunlar.append({
                        "id": str(item.get("id")),
                        "ad": item.get("title"),
                        "aciklama": item.get("description"),
                        "resim": item.get("thumbnail"),
                        "link": item.get("open_giveaway_url"),
                        "deger": item.get("worth"),
                        "bitis": item.get("end_date"),
                        "platform": item.get("platforms") # Hangi mağaza olduğunu da çekelim
                    })
            return oyunlar
        else:
            st.error(f"API Hatası: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
        return []

# --- ARAYÜZ ---
st.title("🎁 Bedava Oyun Avcısı (Steam, Epic, GOG...)")
st.markdown("PC dünyasındaki tüm **%100 indirimli** oyunları (Steam, Epic Games, GOG, Ubisoft vb.) anlık takip eder.")

# Kullanıcı Bilgileri
default_token = "8160497699:AAG2hCZIa_yueqTf3waAUV6r2lXTojUut0A"
default_chat_id = "8355841229"

if "firsat_listesi" not in st.session_state:
    st.session_state.firsat_listesi = []

with st.sidebar:
    st.header("⚙️ Ayarlar")
    tg_token = st.text_input("Bot Token", value=default_token, type="password")
    tg_chat_id = st.text_input("Chat ID", value=default_chat_id)
    st.success("✅ Genişletilmiş Tarama Modu Aktif")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Güncel Fırsatlar")
    
    if st.button("Fırsatları Tara"):
        with st.spinner("Tüm platformlar taranıyor..."):
            sonuc = firsatlari_cek()
            
            if sonuc:
                st.session_state.firsat_listesi = sonuc
                st.success(f"✅ {len(sonuc)} adet oyun bulundu!")
            else:
                st.info("Şu an PC için aktif bir fırsat yok.")

    if st.session_state.firsat_listesi:
        for oyun in st.session_state.firsat_listesi:
            with st.container(border=True):
                col_img, col_text = st.columns([1, 3])
                with col_img:
                    st.image(oyun["resim"], use_column_width=True)
                with col_text:
                    st.subheader(oyun["ad"])
                    st.caption(f"🏢 **{oyun['platform']}** | 💰 Değeri: **{oyun['deger']}**")
                    st.write(f"⏳ Bitiş: {oyun['bitis']}")
                    st.link_button("Oyunu Al 🚀", oyun["link"])

with col2:
    st.subheader("📡 Otomatik Takip")
    dakika = st.slider("Dakika", 15, 240, 60)
    
    if st.button("Takibi Başlat 🚀"):
        if not tg_token or not tg_chat_id:
            st.error("Token bilgileri eksik!")
        else:
            st.success("Avcı Modu Aktif! Tüm PC platformları izleniyor.")
            telegram_gonder(tg_token, tg_chat_id, "🎁 *Süper Avcı Başladı!* \nSteam, Epic, GOG ve diğerleri taranıyor.")
            
            ilk_veri = firsatlari_cek()
            if ilk_veri:
                st.session_state.kayitli_idler = [oyun['id'] for oyun in ilk_veri]
            else:
                st.session_state.kayitli_idler = []

            log_kutusu = st.empty()
            
            while True:
                time.sleep(dakika * 60)
                tarih = datetime.now().strftime('%H:%M')
                
                yeni_liste = firsatlari_cek()
                
                if yeni_liste:
                    yeni_bulunanlar = 0
                    for oyun in yeni_liste:
                        if oyun['id'] not in st.session_state.kayitli_idler:
                            # MESAJ HAZIRLA (Platform bilgisini de ekledik)
                            mesaj = (
                                f"🚨 *BEDAVA OYUN FIRSATI!* 🚨\n\n"
                                f"🎮 *{oyun['ad']}*\n"
                                f"🏢 Platform: {oyun['platform']}\n"
                                f"💰 Değeri: {oyun['deger']}\n"
                                f"⏳ {oyun['bitis']}\n\n"
                                f"[👉 Hemen Kap]({oyun['link']})"
                            )
                            
                            telegram_gonder(tg_token, tg_chat_id, mesaj, oyun['resim'])
                            
                            st.session_state.kayitli_idler.append(oyun['id'])
                            yeni_bulunanlar += 1
                    
                    if yeni_bulunanlar > 0:
                        log_kutusu.success(f"[{tarih}] ✅ {yeni_bulunanlar} yeni oyun!")
                    else:
                        log_kutusu.info(f"[{tarih}] 💤 Yeni fırsat yok.")
                else:
                    log_kutusu.warning(f"[{tarih}] Veri çekilemedi.")

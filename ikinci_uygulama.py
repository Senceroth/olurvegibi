import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="YouTube Haberci", page_icon="▶️", layout="wide")

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

# --- YOUTUBE SON VİDEOYU BULMA (GÜÇLENDİRİLMİŞ VERSİYON) ---
def kanal_son_video_bul(kanal_url):
    # Linki işlem için geçici olarak temizleyelim (/videos kısmını atıp ana sayfaya odaklanalım)
    # Merak etme, listede senin istediğin gibi /videos kalacak, bu sadece RSS bulmak için.
    islem_url = kanal_url
    if "/videos" in islem_url:
        islem_url = islem_url.split("/videos")[0]
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en+FX+419'} 

    try:
        # 1. Adım: Kanal Sayfasına Git
        response = requests.get(islem_url, headers=headers, cookies=cookies, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        
        rss_url = None
        
        # YÖNTEM A: Doğrudan RSS Linki Ara
        rss_link_tag = soup.find("link", {"type": "application/rss+xml"})
        if rss_link_tag:
            rss_url = rss_link_tag['href']
        
        # YÖNTEM B: Bulamazsan Channel ID'yi Çek ve Linki Kendin Yap (IGN/PS için kurtarıcı)
        if not rss_url:
            meta_channel_id = soup.find("meta", {"itemprop": "channelId"})
            if meta_channel_id:
                channel_id = meta_channel_id['content']
                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        if not rss_url:
            return None # İki yöntem de çalışmazsa pes et
            
        # 2. Adım: RSS Beslemesini Oku
        rss_response = requests.get(rss_url, headers=headers, timeout=10)
        rss_soup = BeautifulSoup(rss_response.content, "xml") 
        
        son_video = rss_soup.find("entry")
        
        if son_video:
            video_id = son_video.find("videoId").text
            video_baslik = son_video.find("title").text
            video_link = son_video.find("link")['href']
            kanal_adi = son_video.find("author").find("name").text
            
            return {
                "kanal": kanal_adi,
                "baslik": video_baslik,
                "link": video_link,
                "id": video_id
            }
        return None
        
    except Exception as e:
        print(f"Hata ({kanal_url}): {e}")
        return None

# --- ARAYÜZ ---
st.title("▶️ YouTube Oyun Haberleri")
st.markdown("IGN, PlayStation ve GamingBolt gibi kanalları anlık takip eder.")

# Kullanıcı Bilgileri (Otomatik Dolu)
default_token = "8160497699:AAG2hCZIa_yueqTf3waAUV6r2lXTojUut0A"
default_chat_id = "8355841229"

with st.sidebar:
    st.header("⚙️ Ayarlar")
    tg_token = st.text_input("Bot Token", value=default_token, type="password")
    tg_chat_id = st.text_input("Chat ID", value=default_chat_id)

# Takip Listesi (İstediğin gibi /videos uzantılı)
if "takip_listesi" not in st.session_state:
    st.session_state.takip_listesi = [
        "https://www.youtube.com/@GamingBolt/videos",
        "https://www.youtube.com/@IGN/videos",
        "https://www.youtube.com/@PlayStation/videos"
    ]

if "son_videolar_hafiza" not in st.session_state:
    st.session_state.son_videolar_hafiza = {}

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Takip Edilen Kanallar")
    
    yeni_kanal = st.text_input("Kanal Ekle (Link):", placeholder="https://www.youtube.com/@KanalAdi/videos")
    if st.button("Listeye Ekle"):
        if yeni_kanal and yeni_kanal not in st.session_state.takip_listesi:
            st.session_state.takip_listesi.append(yeni_kanal)
            st.success("Kanal eklendi!")
            st.rerun()

    for kanal in st.session_state.takip_listesi:
        st.code(kanal, language="text")
        
    if st.button("Listeyi Sıfırla"):
        st.session_state.takip_listesi = [
            "https://www.youtube.com/@GamingBolt/videos",
            "https://www.youtube.com/@IGN/videos",
            "https://www.youtube.com/@PlayStation/videos"
        ]
        st.rerun()

with col2:
    st.subheader("📡 Otomatik Takip")
    dakika = st.slider("Kontrol Sıklığı (Dakika)", 1, 60, 5)
    
    if st.button("YouTube Takibini Başlat 🚀"):
        if not tg_token or not tg_chat_id:
            st.error("Token veya Chat ID eksik!")
        else:
            st.success("YouTube Ajanı Devrede! Kanallar taranıyor...")
            telegram_gonder(tg_token, tg_chat_id, "▶️ *YouTube Takibi Başladı!* \nIGN, PlayStation ve GamingBolt izleniyor.")
            
            # İlk açılışta mevcut son videoları hafızaya al
            with st.spinner("Mevcut videolar hafızaya alınıyor..."):
                for url in st.session_state.takip_listesi:
                    veri = kanal_son_video_bul(url)
                    if veri:
                        st.session_state.son_videolar_hafiza[url] = veri['id']
            
            st.info("İlk tarama bitti. Şimdi döngü başlıyor.")
            
            log_kutusu = st.empty()
            
            while True:
                time.sleep(dakika * 60)
                tarih = datetime.now().strftime('%H:%M')
                
                yeni_tespitler = 0
                
                for url in st.session_state.takip_listesi:
                    veri = kanal_son_video_bul(url)
                    
                    if veri:
                        eski_id = st.session_state.son_videolar_hafiza.get(url)
                        yeni_id = veri['id']
                        
                        if yeni_id != eski_id:
                            mesaj = f"🚨 *YENİ VİDEO YAYINLANDI!* 🚨\n\n📺 *{veri['kanal']}*\n▶️ {veri['baslik']}\n\n[İzle]({veri['link']})"
                            telegram_gonder(tg_token, tg_chat_id, mesaj)
                            
                            st.session_state.son_videolar_hafiza[url] = yeni_id
                            yeni_tespitler += 1
                
                if yeni_tespitler > 0:
                    log_kutusu.success(f"[{tarih}] ✅ {yeni_tespitler} yeni video bulundu ve gönderildi!")
                else:
                    log_kutusu.info(f"[{tarih}] 💤 Yeni video yok. Kanallar kontrol edildi.")
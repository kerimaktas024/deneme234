"""
Google Maps Veri Kazıma Scripti

Açıklama:
Bu script, Google Maps üzerinde belirli bir arama terimine göre sonuçları "insan gibi" davranarak çeker ve JSON formatında kaydeder.

Özellikler:
- Rastgele User-Agent kullanımı
- Rastgele zaman uyku (sleep) aralıkları
- Sayfa yüklemesi ve kaydırma (scroll) ile sonuçları dinamik olarak getirir
- İstenen kadar (örn. 2000-3000) kayıt çekmek için kaydırma miktarını ayarlar

Kullanım:
1) Gerekli paketleri yükleyin:
   pip install selenium fake-useragent
2) python google_maps_scraper.py komutuyla çalıştırın. Script çalıştırıldığında:
   - Aranacak bölge/bölge adı
   - İşletme türü
   - Çekilecek kayıt sayısı
   - Çıktı dosyasının kaydedileceği dizin
   bilgilerini soracaktır.

Çıktı:
- "maps_data.json": JSON formatında çekilen veriler
"""
import time, random, json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent  # UserAgent for rastgele tarayıcı tanımlama

# ----------------------
# KULLANICI AYARLARI
# ----------------------
# ARANACAK_TERIM = "restoran İstanbul"    # Google Maps arama terimi (dinamik olarak kullanıcıdan alınacak)
ISTENEN_KAYIT_SAYISI = 2000             # Çekmek istediğiniz toplam kayıt sayısı
SCROLL_PAUSE_TIME = (2, 5)              # Scroll sonrası rastgele uyku aralığı
OUTPUT_DOSYA = "maps_data.json"

# ----------------------
# Yardımcı Fonksiyonlar
# ----------------------
def rastgele_sleep(min_s, max_s):
    """Belirtilen aralıkta rastgele süre uyku"""
    time.sleep(random.uniform(min_s, max_s))

# ----------------------
# Tarayıcı Başlatma
# ----------------------
def surucu_baslat():
    """Headless olmayan, otomasyon algılamayı zorlaştıran Chrome sürücüsü başlatır"""
    ua = UserAgent()
    options = webdriver.ChromeOptions()
    # Headless mod sorun yaratabilir, gerektiğinde kaldırın
    # options.add_argument("--headless")
    options.add_argument(f'user-agent={ua.random}')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # Rastgele pencere boyutu
    width = random.randint(800, 1920)
    height = random.randint(600, 1080)
    options.add_argument(f"--window-size={width},{height}")
    # Chromedriver PATH üzerinden çağrılır
    driver = webdriver.Chrome(options=options)
    # navigator.webdriver özelliğini gizle
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    driver.implicitly_wait(10)
    return driver

# ----------------------
# Google Maps'te Arama ve Kaydırma
# ----------------------
def harita_ara_ve_kaydir(driver, terim, hedef_sayi):
    """Arama terimiyle sonuçları getirir ve yan paneli kaydırarak yeterli kayıt yükler"""
    driver.get("https://www.google.com/maps")
    rastgele_sleep(5, 8)

    # Arama kutusunu bul ve terimi gönder
    arama_box = driver.find_element(By.ID, "searchboxinput")
    arama_box.clear()
    arama_box.send_keys(terim)
    driver.find_element(By.ID, "searchbox-searchbutton").click()
    rastgele_sleep(5, 8)

    # Sonuç panelini bul ve kaydır
    # Panel XPATH veya CSS seçicisini güncelleyin (sitenin yapısına göre değişebilir)
    panel = driver.find_element(By.XPATH, '//div[@role="region" and @aria-label]')
    kayitlar_yuklendi = 0
    while kayitlar_yuklendi < hedef_sayi:
        driver.execute_script('arguments[0].scrollTop += arguments[0].offsetHeight;', panel)
        rastgele_sleep(*SCROLL_PAUSE_TIME)
        # Güncel yüklenen kart sayısını al
        ogeler = panel.find_elements(By.XPATH, './/div[@role="article"]')
        kayitlar_yuklendi = len(ogeler)
        if kayitlar_yuklendi >= hedef_sayi:
            break
    return panel.find_elements(By.XPATH, './/div[@role="article"]')[:hedef_sayi]

# ----------------------
# Veri Çekme
# ----------------------
def veri_cek(driver, ogeler):
    """Her bir sonuç kartından detaylı veriyi toplar"""
    veri_listesi = []
    for idx, ogel in enumerate(ogeler, 1):
        try:
            isim = ogel.find_element(By.XPATH, './/h3').text
        except:
            isim = ""
        try:
            adres = ogel.find_element(By.XPATH, './/span[@class="section-result-location"]').text
        except:
            adres = ""
        try:
            rating = ogel.find_element(By.XPATH, './/span[contains(@aria-label,"Stars")]').get_attribute('aria-label')
        except:
            rating = ""
        veri_listesi.append({
            "isim": isim,
            "adres": adres,
            "puan": rating
        })
        # Kartlar arasında hafif rastgele bekle
        if idx % 20 == 0:
            rastgele_sleep(2, 4)
    return veri_listesi

# ----------------------
# Ana Fonksiyon
# ----------------------
def main():
    # Kullanıcıdan JSON dosyasının kaydedileceği dizini al
    output_dir = input("Lütfen JSON dosyasının kaydedileceği dizini tam yol olarak girin: ")
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, OUTPUT_DOSYA)
    # Kullanıcıdan dinamik giriş bilgisi al
    surucu = surucu_baslat()
    try:
        lokasyon = input("Lütfen aramak istediğiniz bölge/ülkeyi girin: ")
        isletme = input("Hangi işletme türünü aramak istiyorsunuz?: ")
        terim = f"{isletme} {lokasyon}"
        kayit_str = input(f"Kaç kayıt çekmek istiyorsunuz? (varsayılan: {ISTENEN_KAYIT_SAYISI}): ")
        try:
            hedef_sayi = int(kayit_str)
        except ValueError:
            hedef_sayi = ISTENEN_KAYIT_SAYISI
        # Harita sonuçlarını yükle ve çek
        kartlar = harita_ara_ve_kaydir(surucu, terim, hedef_sayi)
        print(f"Yüklü kart sayısı: {len(kartlar)}")
        sonuc = veri_cek(surucu, kartlar)
        # JSON olarak kaydet
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=2)
        print(f"Veri kaydedildi: {output_path}")
    finally:
        surucu.quit()

if __name__ == "__main__":
    main()
# Todo App

[Todo App](https://todo-app-ssot.onrender.com)

Bu uygulama [FastAPI](https://fastapi.tiangolo.com/) ve **Google Gemini AI** kullanılarak geliştirilmiş bir görev yönetim uygulamasıdır. Kullanıcıların girdiği kısa görev başlıklarını ve açıklamalarını Gemini AI kullanarak daha detaylı ve kapsamlı hale dönüştürür.

## Özellikler

*   **Kullanıcı Kimlik Doğrulama:** JWT tabanlı kayıt olma ve giriş yapma sistemi.
*   **Görev Yönetimi (CRUD):** Görev ekleme, listeleme, güncelleme ve silme.
*   **AI Destekli Açıklamalar:** Görev eklerken girilen açıklamalar Gemini 2.5 Flash modeli tarafından otomatik olarak daha zengin hale getirilir.
*   **Web Arayüzü:** Jinja2 ve Bootstrap ile hazırlanmış kullanıcı dostu arayüz.
*   **Veritabanı:** SQLAlchemy ORM ve PostgreSQL.
*   **Docker:** Docker ve Docker Compose ile kolay ayağa kaldırma.

## Kurulum ve Çalıştırma

### Kurulum

1.  **Depoyu klonlayın veya indirin.**
2.  **Sanal ortam oluşturun ve aktif edin:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # -> Linux/Mac
    # .venv\Scripts\activate   # -> Windows
    ```
3.  **Gerekli kütüphaneleri yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **.env dosyasını yapılandırın:**
    Kök dizinde `.env` dosyası oluşturun ve Gemini API anahtarınızı ekleyin:
    ```env
    GEMINI_API_KEY=your_api_key
    ```
5.  **Uygulamayı başlatın:**
    ```bash
    uvicorn main:app --reload
    ```
    Uygulama varsayılan olarak `http://127.0.0.1:8000` adresinde çalışacaktır.

### Docker ile Çalıştırma

Docker yüklü ise tek bir komutla ayağa kaldırabilirsiniz:
```bash
docker-compose up --build
```

## Proje Yapısı

*   `main.py`: Uygulamanın giriş noktası ve FastAPI yapılandırması.
*   `models.py`: SQLAlchemy veritabanı modelleri (Todo, Users).
*   `database.py`: Veritabanı bağlantı ayarları.
*   `routers/`: Uygulamanın API endpoint'leri (Auth, Todo).
*   `templates/`: HTML şablonları.
*   `static/`: CSS ve JS gibi statik dosyalar.

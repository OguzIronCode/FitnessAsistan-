# FitnessAsistan-

Kisisellestirilmis fitness asistani. Bu repo; FastAPI tabanli bir backend API, PyQt tabanli iki masaustu arayuzu ve egzersiz/beslenme veri setlerini icerir.

## Icerik

- [Ozellikler](#ozellikler)
- [Mimari](#mimari)
- [Kurulum](#kurulum)
- [Ortam Degiskenleri](#ortam-degiskenleri)
- [Backend Calistirma](#backend-calistirma)
- [Masaustu Uygulamalari](#masaustu-uygulamalari)
- [API Ozet](#api-ozet)
- [Veri Setleri ve Medya](#veri-setleri-ve-medya)
- [Guvenlik Notlari](#guvenlik-notlari)

## Ozellikler

- Kullanici kayit / giris (Supabase Auth)
- Profil ve hedef hesaplama (TDEE + makro hedefler)
- Ogunsel beslenme takibi ve gunluk makro ozeti
- Besin arama (Supabase cache + Open Food Facts fallback)
- AI asistan (Groq) ile chat ve gunluk motivasyon notu
- Egzersiz programlari (yerel dataset) ve program egzersiz listeleri
- Analitik: gunluk ozet, haftalik performans, PR listesi
- PyQt arayuz: dashboard, beslenme, antrenman, AI, analiz, ayarlar

## Mimari

```
Backend/        -> FastAPI API (Supabase + AI + beslenme)
DesktopApp/     -> Basit PyQt PoC (offline token demo)
PyQt_App/       -> Tam arayuzlu PyQt uygulama
AntrenmanGorselleri/ -> Egzersiz gorselleri
YiyecekGorselleri/   -> Besin gorselleri
```

## Kurulum

On kosullar:

- Python 3.10+
- (Opsiyonel) Supabase projesi ve tablolar

## Ortam Degiskenleri

`Backend/.env` dosyasi olusturun:

```
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
FRONTEND_ORIGIN=http://127.0.0.1:5500

# Opsiyonel (AI)
GROK_API_KEY=...
GROK_MODEL=llama-3.3-70b-versatile
GROK_ENDPOINT=https://api.groq.com/openai/v1/chat/completions

# Opsiyonel (Fatsecret entegrasyonu icin hazir alanlar)
FATSECRET_CLIENT_ID=
FATSECRET_CLIENT_SECRET=
```

Not: `.env` repo disinda tutulur. Ornek degerleri paylasmayin.

## Backend Calistirma

```
cd Backend
pip install -r requirements.txt
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API dokumantasyonu:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Masaustu Uygulamalari

### DesktopApp (PoC)

Basit giris ve sekmeli UI. Bu PoC su an offline token ile calisir.

```
cd DesktopApp
pip install -r requirements.txt
py main.py
```

### PyQt_App (Ana arayuz)

Backend calisiyor olmali.

```
cd PyQt_App
pip install -r requirements.txt
py main.py
```

## API Ozet

Kisa endpoint listesi (tam liste icin /docs):

- `POST /api/auth/register` -> kayit
- `POST /api/auth/login` -> giris
- `POST /api/auth/logout` -> cikis

- `GET /api/user/profile` -> profil getir
- `POST /api/user/profile` -> profil olustur
- `PUT /api/user/profile` -> profil guncelle

- `GET /api/food/search` -> besin ara
- `GET /api/food/{id}` -> besin detayi
- `GET /api/food/barcode/{barcode}` -> barkod sorgu

- `GET /api/meals?date=YYYY-MM-DD` -> gunluk ogunler
- `POST /api/meals` -> ogun ekle
- `GET /api/meals/summary?date=YYYY-MM-DD` -> gunluk makro

- `GET /api/workouts` -> antrenman listesi
- `POST /api/workouts` -> antrenman olustur
- `POST /api/workouts/sets` -> set kaydet
- `GET /api/workouts/{id}/sets` -> set listesi

- `GET /api/analytics/summary` -> dashboard ozet
- `GET /api/analytics/weekly-performance` -> haftalik performans
- `GET /api/analytics/personal-records` -> PR listesi

- `POST /api/ai/chat` -> AI chat
- `GET /api/ai/daily-tip` -> gunluk tip
- `POST /api/ai/generate-meal-plan` -> beslenme plani
- `POST /api/ai/generate-exercises` -> program egzersizleri

- `GET /api/exercises/programs` -> program listesi (dataset)
- `GET /api/exercises/suggest` -> rastgele egzersizler

## Veri Setleri ve Medya

- `Backend/data/antrenman_dataset.json` program/egzersiz kaynagi
- `Backend/data/beslenme_dataset.json` beslenme ornekleri
- `AntrenmanGorselleri/` ve `PyQt_App/assets/exercises/` egzersiz gorselleri
- `YiyecekGorselleri/` besin gorselleri (lokal fallback)

## Guvenlik Notlari

- `.env` ve API anahtarlarini repo’ya koymayin.
- Uretim ortaminda `SECRET_KEY` ve token ayarlarini guclendirin.
- Supabase service role key’i sadece backend tarafinda kullanin.

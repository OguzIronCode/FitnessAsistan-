# FitnessAsistani

<div align="center">
  <img src="FitnessAsistani_Logo.png" alt="FitnessAsistani Logo" width="180"/>

  <br/>

  **Kişiselleştirilmiş yapay zeka destekli fitness ve beslenme takip uygulaması**

  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
  ![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-purple?logo=qt)
  ![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase)
  ![Groq](https://img.shields.io/badge/AI-Groq%20LLaMA--3.3--70B-orange)
  ![License](https://img.shields.io/badge/lisans-MIT-lightgrey)
</div>

---

## İçindekiler

- [Proje Hakkında](#proje-hakkında)
- [Özellikler](#özellikler)
- [Mimari](#mimari)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Veritabanı Şeması](#veritabanı-şeması)
- [API Referansı](#api-referansı)
- [Kurulum](#kurulum)
- [Ortam Değişkenleri](#ortam-değişkenleri)
- [Çalıştırma](#çalıştırma)
- [Proje Yapısı](#proje-yapısı)
- [Ekran Görüntüleri](#ekran-görüntüleri)
- [Veri Setleri ve Medya](#veri-setleri-ve-medya)
- [Güvenlik Notları](#güvenlik-notları)
- [Katkıda Bulunma](#katkıda-bulunma)

---

## Proje Hakkında

**FitnessAsistani**, kullanıcıların beslenme ve antrenman verilerini takip etmelerine, hedef belirlemelerine ve yapay zeka destekli önerilere ulaşmalarına olanak tanıyan kapsamlı bir masaüstü fitness uygulamasıdır.

Uygulama; Harris-Benedict formülüne dayalı **TDEE (Toplam Günlük Enerji Harcaması)** ve makro besin hedefi hesaplama, öğün bazlı kalori takibi, antrenman kaydı, vücut metriği izleme ve **Groq (LLaMA-3.3-70B)** entegrasyonu ile AI destekli önerileri tek bir arayüzde birleştirir.

**Temel bileşenler:**
| Bileşen | Açıklama |
|---|---|
| `Backend/` | FastAPI tabanlı REST API; kimlik doğrulama, beslenme, antrenman ve AI uç noktalarını yönetir |
| `PyQt_App/` | Tam özellikli, karanlık temalı PyQt6 masaüstü uygulaması |
| `DesktopApp/` | Basit PyQt6 PoC (kavram kanıtı) arayüzü |

---

## Özellikler

### Kimlik Doğrulama ve Kullanıcı Yönetimi
- Supabase Auth ile güvenli kayıt ve giriş akışı
- JWT tabanlı oturum yönetimi (`ACCESS_TOKEN_EXPIRE_MINUTES` yapılandırılabilir)
- Harris-Benedict formülü ile otomatik **TDEE ve makro hedef hesaplama**
  - Aktivite seviyesi çarpanları (hareketsiz → çok aktif)
  - Hedefe göre ayarlama: kilo verme (kesim), kilo alma (hacim), idame
- Profil bilgileri: boy, kilo, yaş, cinsiyet, aktivite seviyesi, beslenme tercihi

### Beslenme Takibi
- **Çift kaynaklı besin arama**: önce Supabase önbelleği, bulunamazsa Open Food Facts API
- Barkod ile besin sorgulama
- Öğün türüne göre kayıt: kahvaltı, öğle, akşam, ara öğün
- Günlük makro özeti: kalori, protein, karbonhidrat, yağ
- Günlük öğün bölme: 3, 4 veya 5 öğün seçeneği
- Tüketilen besinlerin geçmişe dönük görüntülenmesi

### Antrenman Takibi
- Antrenman oluşturma ve kaydetme
- Yerel JSON veri setinden **150+ egzersiz programı** atama
- Set, tekrar ve ağırlık kaydı
- Antrenman süresi takibi
- Kişisel rekor (PR) yönetimi
- Egzersiz önerisi

### AI Asistan (Groq – LLaMA-3.3-70B)
- Serbest sohbet: beslenme ve antrenman sorularını yanıtlar
- **Günlük motivasyon notu** otomatik olarak oluşturulur
- Beslenme tercihine ve hedefe göre **özel öğün planı** üretimi (vejetaryen, vegan, normal)
- Hedef ve kas grubuna göre **özel egzersiz programı** oluşturma
- Tüm AI yanıtları Türkçe olarak yapılandırılmıştır

### Analitik ve Raporlama
- Günlük özet dashboard: kalori durumu, makro yüzdeleri, tamamlanan antrenmanlar
- Haftalık performans metrikleri (kalori trendi, antrenman sıklığı)
- Kişisel rekorlar listesi (PR)
- Vücut metriği takibi: kilo, vücut yağ oranı (%), kas oranı (%)
- Matplotlib ile görsel haftalık grafik

### Arayüz (PyQt_App)
- Modern karanlık tema (özel renk paleti)
- 6 bölümlü sol kenar çubuğu navigasyonu: Ana Sayfa, Beslenme, Antrenman, AI, Analitik, Ayarlar
- Toast bildirimleri
- Profil açılır menüsü
- Sekmeli gezinti
- Gerçek zamanlı veri görselleştirme

---

## Mimari

```
FitnessAsistan-/
├── Backend/                   ← FastAPI REST API
│   ├── main.py                ← Uygulama girişi, CORS, router kayıtları
│   ├── config.py              ← Pydantic Settings (.env yönetimi)
│   ├── routers/               ← Endpoint grupları
│   │   ├── auth.py            ← Kayıt, giriş, çıkış
│   │   ├── user.py            ← Profil CRUD
│   │   ├── food.py            ← Besin arama ve barkod
│   │   ├── meals.py           ← Öğün kayıt ve özeti
│   │   ├── workouts.py        ← Antrenman ve set yönetimi
│   │   ├── analytics.py       ← Dashboard, haftalık, PR
│   │   ├── ai.py              ← Groq AI entegrasyonu
│   │   └── exercises.py       ← Program listesi (dataset)
│   ├── models/
│   │   └── schemas.py         ← Tüm Pydantic şemaları
│   ├── utils/
│   │   ├── auth.py            ← Token doğrulama (Supabase)
│   │   └── openfoodfacts.py   ← Open Food Facts istemcisi
│   ├── db/
│   │   └── supabase.py        ← Supabase istemci başlatma
│   ├── data/
│   │   ├── antrenman_dataset.json
│   │   └── beslenme_dataset.json
│   └── scripts/
│       └── supabase_schema.sql ← Veritabanı şeması ve RLS politikaları
│
├── PyQt_App/                  ← Ana masaüstü uygulaması
│   ├── main.py                ← Uygulama girişi
│   ├── theme.py               ← Renk paleti ve stil tanımları
│   ├── state.py               ← Global uygulama durumu (token, user_id)
│   ├── api.py                 ← Thread destekli API istemcisi
│   ├── pages/
│   │   ├── home.py            ← Dashboard sayfası
│   │   ├── login.py           ← Giriş/kayıt
│   │   ├── profile.py         ← Profil oluşturma/düzenleme
│   │   ├── nutrition.py       ← Beslenme takibi
│   │   ├── workout.py         ← Antrenman takibi
│   │   ├── ai_chat.py         ← AI sohbet arayüzü
│   │   ├── analytics.py       ← Analitik sayfası
│   │   └── settings.py        ← Ayarlar
│   └── widgets/
│       ├── sidebar.py         ← Navigasyon kenar çubuğu
│       ├── stat_card.py       ← İstatistik kart bileşeni
│       └── toast.py           ← Bildirim bileşeni
│
├── DesktopApp/                ← PoC arayüzü (offline demo)
│   ├── main.py
│   ├── api.py
│   └── ui/
│
├── AntrenmanGorselleri/       ← 150+ egzersiz görseli (.jpg)
├── YiyecekGorselleri/         ← 32 besin görseli (.jpg)
├── nihai_antrenman_dataset.json
└── FitnessAsistani_Logo.png
```

### Veri Akışı

```
PyQt_App
    │
    │  HTTP (requests + thread)
    ▼
Backend (FastAPI @ localhost:8000)
    │
    ├──► Supabase (PostgreSQL + Auth)   ← kullanıcı verileri, besin önbelleği
    ├──► Open Food Facts API             ← besin veritabanı (fallback)
    └──► Groq API (LLaMA-3.3-70B)       ← AI önerileri ve sohbet
```

---

## Teknoloji Yığını

### Backend
| Kütüphane | Sürüm | Amaç |
|---|---|---|
| FastAPI | 0.115.5 | REST API çerçevesi |
| Uvicorn | 0.32.1 | ASGI sunucu |
| Pydantic | 2.10.3 | Veri doğrulama ve şema |
| pydantic-settings | 2.6.1 | `.env` ile yapılandırma yönetimi |
| supabase | 2.10.0 | Supabase Python istemcisi |
| httpx | 0.27.2 | Asenkron HTTP istemcisi (Open Food Facts) |
| python-multipart | 0.0.12 | Çok parçalı form desteği |

### Masaüstü Uygulaması (PyQt_App)
| Kütüphane | Sürüm | Amaç |
|---|---|---|
| PyQt6 | ≥ 6.6.0 | GUI çerçevesi |
| requests | ≥ 2.31.0 | Backend ile HTTP iletişimi |
| matplotlib | ≥ 3.8.0 | Haftalık veri grafikleri |

### Altyapı ve Servisler
| Servis | Kullanım Amacı |
|---|---|
| **Supabase** | PostgreSQL veritabanı, kimlik doğrulama, satır düzeyinde güvenlik (RLS) |
| **Groq API** | LLaMA-3.3-70B modeliyle AI önerileri ve sohbet |
| **Open Food Facts** | Açık kaynaklı besin veritabanı (barkod ve isim araması) |

---

## Veritabanı Şeması

Şema dosyası: [`Backend/scripts/supabase_schema.sql`](Backend/scripts/supabase_schema.sql)

### Tablolar

#### `profiles`
Kullanıcı profil bilgileri ve hesaplanan hedefler.
| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | UUID (PK) | Supabase `auth.users` ile eşleşir |
| `username` | TEXT | Görünen ad |
| `height_cm` | FLOAT | Boy (cm) |
| `weight_kg` | FLOAT | Kilo (kg) |
| `age` | INTEGER | Yaş |
| `gender` | TEXT | `male` / `female` |
| `activity_level` | TEXT | `sedentary` … `very_active` |
| `goal` | TEXT | `cut` / `bulk` / `maintain` |
| `diet_preference` | TEXT | `normal` / `vegetarian` / `vegan` |
| `target_calories` | INTEGER | Hesaplanan günlük kalori hedefi |
| `target_protein_g` | INTEGER | Günlük protein hedefi (g) |
| `target_carbs_g` | INTEGER | Günlük karbonhidrat hedefi (g) |
| `target_fat_g` | INTEGER | Günlük yağ hedefi (g) |
| `meals_per_day` | INTEGER | Öğün sayısı tercihi (3–5) |

#### `foods`
Besin önbelleği (Open Food Facts'tan alınan ve yerel kayıtlar).
| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | UUID (PK) | Benzersiz besin kimliği |
| `name` | TEXT | Besin adı |
| `barcode` | TEXT | Barkod numarası (opsiyonel) |
| `calories_per_100g` | FLOAT | 100g başına kalori |
| `protein_per_100g` | FLOAT | 100g başına protein (g) |
| `carbs_per_100g` | FLOAT | 100g başına karbonhidrat (g) |
| `fat_per_100g` | FLOAT | 100g başına yağ (g) |
| `source` | TEXT | `supabase` / `openfoodfacts` |

#### `meals`
Günlük öğün kayıtları.
| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | UUID (PK) | Kayıt kimliği |
| `user_id` | UUID (FK) | `profiles.id` |
| `food_id` | UUID (FK) | `foods.id` |
| `meal_type` | TEXT | `breakfast` / `lunch` / `dinner` / `snack` |
| `date` | DATE | Tüketim tarihi |
| `amount_g` | FLOAT | Miktar (gram) |
| `calories` | FLOAT | Tüketilen kalori |
| `protein_g` | FLOAT | Tüketilen protein (g) |
| `carbs_g` | FLOAT | Tüketilen karbonhidrat (g) |
| `fat_g` | FLOAT | Tüketilen yağ (g) |

#### `workouts`
Antrenman seansları.
| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | UUID (PK) | Antrenman kimliği |
| `user_id` | UUID (FK) | `profiles.id` |
| `program_id` | TEXT | Dataset'teki program kimliği |
| `name` | TEXT | Antrenman adı |
| `date` | TIMESTAMPTZ | Antrenman zamanı |
| `duration_minutes` | INTEGER | Süre (dakika) |
| `notes` | TEXT | Kullanıcı notları |

#### `workout_sets`
Antrenman içindeki bireysel setler.
| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | UUID (PK) | Set kimliği |
| `workout_id` | UUID (FK) | `workouts.id` |
| `exercise_name` | TEXT | Egzersiz adı |
| `set_number` | INTEGER | Set sırası |
| `reps` | INTEGER | Tekrar sayısı |
| `weight_kg` | FLOAT | Ağırlık (kg) |

#### `body_metrics`
Vücut ölçüm geçmişi.
| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | UUID (PK) | Ölçüm kimliği |
| `user_id` | UUID (FK) | `profiles.id` |
| `date` | DATE | Ölçüm tarihi |
| `weight_kg` | FLOAT | Kilo (kg) |
| `body_fat_pct` | FLOAT | Vücut yağ oranı (%) |
| `muscle_pct` | FLOAT | Kas oranı (%) |

> **Güvenlik:** Tüm tablolar Supabase **Row Level Security (RLS)** politikalarıyla korunmaktadır; kullanıcılar yalnızca kendi verilerine erişebilir.

---

## API Referansı

Tam interaktif dokümantasyon için backend çalışırken şu adresleri ziyaret edin:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Kimlik Doğrulama (`/api/auth`)

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `POST` | `/api/auth/register` | Yeni kullanıcı oluşturur |
| `POST` | `/api/auth/login` | Giriş yapar, JWT token döner |
| `POST` | `/api/auth/logout` | Oturumu sonlandırır |

**Kayıt isteği örneği:**
```json
{
  "email": "kullanici@ornek.com",
  "password": "güçlüŞifre123",
  "username": "oguzhan"
}
```

**Giriş yanıtı örneği:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "uuid-here"
}
```

### Kullanıcı Profili (`/api/user`)

Tüm istekler `Authorization: Bearer <token>` başlığı gerektirir.

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/user/profile` | Profil bilgilerini getirir |
| `POST` | `/api/user/profile` | Yeni profil oluşturur |
| `PUT` | `/api/user/profile` | Profil günceller |

**Profil oluşturma isteği örneği:**
```json
{
  "username": "oguzhan",
  "height_cm": 180,
  "weight_kg": 80,
  "age": 25,
  "gender": "male",
  "activity_level": "moderately_active",
  "goal": "cut",
  "diet_preference": "normal",
  "meals_per_day": 4
}
```

**Yanıt:** Hesaplanan `target_calories`, `target_protein_g`, `target_carbs_g`, `target_fat_g` alanlarını içerir.

### Besin (`/api/food`)

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/food/search?q={isim}` | Besin adına göre arar |
| `GET` | `/api/food/{id}` | Besin detayını getirir |
| `GET` | `/api/food/barcode/{barcode}` | Barkoda göre besin sorgular |

**Arama akışı:** Supabase önbelleğinde bulunamazsa Open Food Facts API'sine istek atılır ve önbelleğe kaydedilir.

### Öğünler (`/api/meals`)

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/meals?date=YYYY-MM-DD` | Güne ait öğünleri listeler |
| `POST` | `/api/meals` | Yeni öğün kaydeder |
| `GET` | `/api/meals/summary?date=YYYY-MM-DD` | Günlük makro özetini döner |

**Öğün ekleme isteği örneği:**
```json
{
  "food_id": "uuid-here",
  "meal_type": "breakfast",
  "date": "2026-05-31",
  "amount_g": 200
}
```

**Özet yanıtı örneği:**
```json
{
  "total_calories": 1850,
  "total_protein_g": 145,
  "total_carbs_g": 180,
  "total_fat_g": 60,
  "target_calories": 2200,
  "meals": [...]
}
```

### Antrenmanlar (`/api/workouts`)

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/workouts` | Kullanıcının antrenman listesini döner |
| `POST` | `/api/workouts` | Yeni antrenman oluşturur |
| `GET` | `/api/workouts/{id}` | Antrenman detayını döner |
| `DELETE` | `/api/workouts/{id}` | Antrenmanı siler |
| `POST` | `/api/workouts/sets` | Antrenmana set ekler |
| `GET` | `/api/workouts/{id}/sets` | Antrenmanın setlerini listeler |

### Analitik (`/api/analytics`)

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/analytics/summary` | Günlük dashboard özeti |
| `GET` | `/api/analytics/weekly-performance` | Haftalık kalori ve antrenman trendi |
| `GET` | `/api/analytics/personal-records` | Kişisel rekorlar listesi |

### AI Asistan (`/api/ai`)

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `POST` | `/api/ai/chat` | AI ile serbest sohbet |
| `GET` | `/api/ai/daily-tip` | Günlük motivasyon notu |
| `POST` | `/api/ai/generate-meal-plan` | Hedefe özel öğün planı üretir |
| `POST` | `/api/ai/generate-exercises` | Hedefe özel egzersiz programı üretir |

**Öğün planı isteği örneği:**
```json
{
  "goal": "cut",
  "diet_preference": "vegetarian",
  "target_calories": 1800,
  "meals_per_day": 4
}
```

**Egzersiz programı isteği örneği:**
```json
{
  "goal": "muscle_gain",
  "muscle_groups": ["göğüs", "sırt", "omuz"],
  "sessions_per_week": 4
}
```

### Egzersizler (`/api/exercises`)

| Method | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/api/exercises/programs` | Yerel dataset'teki tüm programları listeler |
| `GET` | `/api/exercises/suggest` | Rastgele egzersiz önerileri döner |

---

## Kurulum

### Ön Koşullar

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Supabase hesabı** — [supabase.com](https://supabase.com) (ücretsiz plan yeterlidir)
- **Groq API anahtarı** (opsiyonel, AI özellikleri için) — [console.groq.com](https://console.groq.com)

### 1. Repoyu Klonlayın

```bash
git clone https://github.com/OguzHAN/FitnessAsistan-.git
cd FitnessAsistan-
```

### 2. Supabase Veritabanını Hazırlayın

1. [Supabase Dashboard](https://app.supabase.com) üzerinden yeni bir proje oluşturun.
2. **SQL Editor** bölümüne gidin.
3. [`Backend/scripts/supabase_schema.sql`](Backend/scripts/supabase_schema.sql) dosyasının tamamını kopyalayıp çalıştırın.
4. Bu işlem tablolar, indeksler ve RLS politikalarını otomatik olarak oluşturur.

### 3. Backend Bağımlılıklarını Yükleyin

```bash
cd Backend
pip install -r requirements.txt
```

### 4. PyQt_App Bağımlılıklarını Yükleyin

```bash
cd PyQt_App
pip install -r requirements.txt
```

---

## Ortam Değişkenleri

`Backend/` klasöründe `.env` adında bir dosya oluşturun:

```env
# ─── Supabase ─────────────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...

# ─── JWT ──────────────────────────────────────────────
SECRET_KEY=cok-guclu-bir-gizli-anahtar-buraya
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080   # 7 gün

# ─── CORS ─────────────────────────────────────────────
FRONTEND_ORIGIN=http://127.0.0.1:5500

# ─── AI (opsiyonel) ───────────────────────────────────
GROK_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROK_MODEL=llama-3.3-70b-versatile
GROK_ENDPOINT=https://api.groq.com/openai/v1/chat/completions

# ─── FatSecret (opsiyonel, hazırlık aşamasında) ───────
FATSECRET_CLIENT_ID=
FATSECRET_CLIENT_SECRET=
```

> **Dikkat:** `.env` dosyasını kesinlikle git'e eklemeyin. Dosya zaten `.gitignore` tarafından dışlanmaktadır.

### Değişken Açıklamaları

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `SUPABASE_URL` | Evet | Supabase projenizin URL'si |
| `SUPABASE_ANON_KEY` | Evet | Supabase anonim (public) API anahtarı |
| `SUPABASE_SERVICE_ROLE_KEY` | Evet | Supabase servis rolü anahtarı (RLS bypass için backend'de) |
| `SECRET_KEY` | Evet | JWT imzalama için gizli anahtar |
| `ALGORITHM` | Evet | JWT algoritması (varsayılan: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Evet | Token geçerlilik süresi (dakika) |
| `FRONTEND_ORIGIN` | Evet | İzin verilen CORS kaynağı |
| `GROK_API_KEY` | Hayır | Groq API anahtarı (AI özellikler için gerekli) |
| `GROK_MODEL` | Hayır | Kullanılacak Groq modeli |
| `GROK_ENDPOINT` | Hayır | Groq API uç noktası |

---

## Çalıştırma

### Backend'i Başlatın

```bash
cd Backend
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Başarılı başlatmada terminalde şunu görmelisiniz:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

API dokümantasyonu:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/

### PyQt_App'i Başlatın (Ana Uygulama)

Backend çalışır durumdayken yeni bir terminal açın:

```bash
cd PyQt_App
py main.py
```

### DesktopApp'i Başlatın (PoC)

```bash
cd DesktopApp
pip install -r requirements.txt
py main.py
```

> **Not:** DesktopApp, offline token demosu içeren basit bir kavram kanıtı uygulamasıdır. Tam özellikler için `PyQt_App` kullanın.

---

## Proje Yapısı

```
FitnessAsistan-/
│
├── Backend/
│   ├── main.py                    # FastAPI giriş noktası
│   ├── config.py                  # Pydantic Settings yapılandırması
│   ├── requirements.txt           # Python bağımlılıkları
│   │
│   ├── routers/
│   │   ├── auth.py                # POST /register, /login, /logout
│   │   ├── user.py                # GET/POST/PUT /user/profile
│   │   ├── food.py                # Besin arama, barkod
│   │   ├── meals.py               # Öğün CRUD ve günlük özet
│   │   ├── workouts.py            # Antrenman ve set yönetimi
│   │   ├── analytics.py           # Analitik uç noktaları
│   │   ├── ai.py                  # Groq AI entegrasyonu
│   │   └── exercises.py           # Egzersiz dataset uç noktaları
│   │
│   ├── models/
│   │   └── schemas.py             # Tüm request/response Pydantic şemaları
│   │
│   ├── utils/
│   │   ├── auth.py                # Supabase token doğrulama
│   │   ├── openfoodfacts.py       # Open Food Facts API istemcisi
│   │   └── fatsecret.py           # FatSecret (hazırlık)
│   │
│   ├── db/
│   │   ├── supabase.py            # Supabase istemci başlatma
│   │   └── local_supabase.py      # Yerel test yardımcıları
│   │
│   ├── data/
│   │   ├── antrenman_dataset.json # Egzersiz programları
│   │   └── beslenme_dataset.json  # Beslenme referans verileri
│   │
│   └── scripts/
│       └── supabase_schema.sql    # Veritabanı şeması ve RLS
│
├── PyQt_App/
│   ├── main.py                    # Uygulama giriş noktası
│   ├── theme.py                   # Karanlık tema renk paleti
│   ├── state.py                   # Global durum yönetimi
│   ├── api.py                     # Thread destekli HTTP istemcisi
│   ├── requirements.txt
│   │
│   ├── pages/
│   │   ├── home.py                # Dashboard (istatistikler, grafik)
│   │   ├── login.py               # Giriş/kayıt ekranı
│   │   ├── profile.py             # Profil formu
│   │   ├── nutrition.py           # Öğün takip sayfası
│   │   ├── workout.py             # Antrenman takip sayfası
│   │   ├── ai_chat.py             # AI sohbet ekranı
│   │   ├── analytics.py           # Analitik ve raporlama
│   │   └── settings.py            # Uygulama ayarları
│   │
│   └── widgets/
│       ├── sidebar.py             # Sol navigasyon çubuğu
│       ├── stat_card.py           # İstatistik kart bileşeni
│       └── toast.py               # Toast bildirim sistemi
│
├── DesktopApp/                    # PoC (kavram kanıtı) arayüzü
│   ├── main.py
│   ├── api.py
│   └── ui/
│
├── AntrenmanGorselleri/           # 150+ egzersiz görseli (.jpg)
├── YiyecekGorselleri/             # 32 besin görseli (.jpg)
├── nihai_antrenman_dataset.json   # Antrenman dataset (kök)
└── FitnessAsistani_Logo.png
```

---

## Ekran Görüntüleri

> Uygulamanın arayüz sayfaları:

| Sayfa | Açıklama |
|---|---|
| **Giriş / Kayıt** | E-posta ve şifre ile Supabase Auth üzerinden kimlik doğrulama |
| **Profil Oluşturma** | Boy, kilo, yaş, aktivite seviyesi ve hedef girişi; TDEE otomatik hesaplanır |
| **Dashboard** | Günlük kalori durumu, makro kartları, haftalık grafik, son öğünler |
| **Beslenme** | Besin arama (isim/barkod), öğün tipi seçimi, günlük makro takibi |
| **Antrenman** | Program atama, set/tekrar/ağırlık kaydı, antrenman süresi |
| **AI Sohbet** | Groq destekli serbest sohbet, günlük motivasyon, öğün ve egzersiz planı üretimi |
| **Analitik** | Haftalık performans grafikleri, kişisel rekorlar, vücut metriği geçmişi |

---

## Veri Setleri ve Medya

| Kaynak | Konum | İçerik |
|---|---|---|
| Egzersiz dataset | `Backend/data/antrenman_dataset.json` | 150+ egzersiz içeren program şablonları |
| Beslenme dataset | `Backend/data/beslenme_dataset.json` | Temel besin referans verileri |
| Egzersiz görselleri | `AntrenmanGorselleri/` ve `PyQt_App/assets/exercises/` | Her egzersiz için JPG |
| Besin görselleri | `YiyecekGorselleri/` | 32 yaygın besin için JPG |
| Open Food Facts | Harici API | 3 milyondan fazla ürün veritabanı (barkod desteği dahil) |

---

## Güvenlik Notları

- `.env` dosyasını ve API anahtarlarını **kesinlikle** repository'ye eklemeyin.
- Üretim ortamında `SECRET_KEY` değerini en az 32 karakter uzunluğunda rastgele bir değerle değiştirin.
- `SUPABASE_SERVICE_ROLE_KEY`, RLS politikalarını bypass ettiğinden yalnızca backend sunucu tarafında kullanılmalıdır; istemci uygulamalarına hiçbir zaman gönderilmemelidir.
- Supabase Dashboard üzerinden **Email Confirmations** özelliğini etkinleştirmeniz önerilir.
- CORS `FRONTEND_ORIGIN` değerini yalnızca güvendiğiniz kaynaklarla sınırlı tutun.
- Üretim dağıtımı için `--reload` bayrağını kaldırın ve bir process manager (ör. `gunicorn`, `supervisor`) kullanın.

---

## Katkıda Bulunma

1. Bu repoyu fork edin
2. Yeni bir branch oluşturun: `git checkout -b ozellik/yeni-ozellik`
3. Değişikliklerinizi commit edin: `git commit -m "feat: yeni özellik ekle"`
4. Branch'ınızı push edin: `git push origin ozellik/yeni-ozellik`
5. Pull Request açın

---

## Lisans

Bu proje [MIT Lisansı](LICENSE) altında dağıtılmaktadır.

---

<div align="center">
  Geliştirici: <strong>OguzHAN</strong> · oguzzh4nn@gmail.com
</div>

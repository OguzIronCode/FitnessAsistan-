"""
Egzersiz adını → görsel yolu eşleştiren modül.
Görseller assets/exercises/ klasöründe {ad}_alt{n}.jpg formatında.
"""
import os
import re
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets" / "exercises"

# ── Türkçe → İngilizce egzersiz çeviri sözlüğü ───────────────────────────────
TR_TO_EN = {
    "Bacak Kırma":                    "Bacak Kırma",
    "Bacak Kırma Makinesi":           "Bacak Kırma Makinesi",
    "Bacak Kıvrımı":                  "Bacak Kıvrımı",
    "Kol Kırma":                      "Bicep Curl",
    "Omuz Kırma":                     "Arnold Press",
    "Kaburgalar":                     "Barbell Row",
    "Bacak Öne Kaldırma":             "Bacak Öne Kaldırma",
    "Bacakların Gücü":                "Bacakların Gücü",
    "Ağırlıklı Barfiks":              "Ağırlıklı Barfiks",
    "Ağırlıklı Dips":                 "Ağırlıklı Dips",
    "Bacak Kaldırma":                 "Bacak Kaldırma",
    "Bacak Kaldırma Egzersizi":       "Bacak Kaldırma Egzersizi",
    "Kuvvetli Çekme Makinesi":        "Bentover Row",
    "Kollar":                         "Bicep Curl",
    "Omuz Kaldıraç":                  "Barbell Overhead Press",
    "Koşu":                           "Air Bike",
    "Squat":                          "Air Squat",
    "Deadlift":                       "Deadlift",
    "Bench Press":                    "Bench Press",
    "Pull-up":                        "Assisted Pull-Up",
    "Goblet Squat":                   "Belt Squat",
    "Lunge":                          "Cossack Squat",
    "Hip Thrust":                     "Barbell Floor Press",
    "Plank":                          "Abs Wheel Rollout",
    "Burpees":                        "Burpees",
    "High Knees":                     "Air Bike",
    "Knee Push-Up":                   "Assisted Close-Grip Push-Up",
    "Kettlebell Swing":               "At-Home Workouts (Kettlebell)",
    "Kettlebell Press":               "Arnold Press",
    "Kettlebell Deadlift":            "Deadlift",
    "Kettlebell Clean and Press":     "Atlas Stones",
    "Row":                            "Barbell Row",
    "Lat Raise":                      "Cable Lateral Raise",
    "Romanian Deadlift":              "Conventional Barbell Deadlift",
}

# ── Mevcut görsel adlarının index'i ───────────────────────────────────────────
def _build_index() -> dict[str, Path]:
    """Klasördeki tüm görselleri normalize edilmiş ada göre indexle."""
    index: dict[str, Path] = {}
    if not ASSETS_DIR.exists():
        return index
    for img in ASSETS_DIR.glob("*.jpg"):
        # "Bench Press_alt2.jpg" → "bench press"
        base = re.sub(r"_alt\d+$", "", img.stem).strip().lower()
        # Her egzersiz için ilk görsel (en küçük alt numarası) öncelikli
        if base not in index:
            index[base] = img
        else:
            # Daha küçük alt numaralı olanı tercih et
            existing_alt = re.search(r"_alt(\d+)$", index[base].stem)
            new_alt      = re.search(r"_alt(\d+)$", img.stem)
            if existing_alt and new_alt:
                if int(new_alt.group(1)) < int(existing_alt.group(1)):
                    index[base] = img
    return index


_IMAGE_INDEX: dict[str, Path] = _build_index()


def _normalize(name: str) -> str:
    return name.strip().lower()


def find_image(exercise_name: str) -> str | None:
    """
    Egzersiz adına karşılık gelen görsel yolunu döndür.
    Bulunamazsa None döner.
    """
    if not exercise_name:
        return None

    # 1) Doğrudan sözlük çevirisi
    translated = TR_TO_EN.get(exercise_name, exercise_name)
    key = _normalize(translated)
    if key in _IMAGE_INDEX:
        return str(_IMAGE_INDEX[key])

    # 2) Orijinal adla tam eşleşme
    key = _normalize(exercise_name)
    if key in _IMAGE_INDEX:
        return str(_IMAGE_INDEX[key])

    # 3) Kısmi eşleşme — indexteki her ada karşı
    for idx_key, path in _IMAGE_INDEX.items():
        if key in idx_key or idx_key in key:
            return str(path)

    # 4) Tek kelime eşleşmesi
    words = [w for w in key.split() if len(w) > 3]
    for idx_key, path in _IMAGE_INDEX.items():
        if any(w in idx_key for w in words):
            return str(path)

    return None


def all_images() -> dict[str, str]:
    """Tüm mevcut görsellerin {normalize_ad: yol} sözlüğü."""
    return {k: str(v) for k, v in _IMAGE_INDEX.items()}

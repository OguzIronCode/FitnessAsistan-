from fastapi import APIRouter, HTTPException, Query, Depends
from utils.auth import get_current_user
from typing import Optional
import random
import json
import os
import re

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

# ── Dataset Yükleme ───────────────────────────────────────────────────────────
_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "antrenman_dataset.json")


def _load_dataset() -> list[dict]:
    try:
        with open(_DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _map_level(hedef) -> str:
    if isinstance(hedef, list):
        hedef = " ".join(str(h) for h in hedef)
    h = str(hedef).lower()
    if "ileri" in h and "başlangıç" in h:
        return "All Levels"
    if "ileri" in h:
        return "Advanced"
    if "orta" in h and "başlangıç" in h:
        return "Intermediate"
    if "orta" in h:
        return "Intermediate"
    return "Beginner"


def _map_goal(name: str) -> str:
    n = name.lower()
    # Powerbuilding / Güç odaklı
    if any(k in n for k in [
        "kuvvet", "güç", "powerlifting", "powerbuilding",
        "deadlift", "squat", "halter", "olympic",
        "strongman", "ağırlık kaldırma",
    ]):
        return "Powerbuilding"
    # Kardiyo / Yağ yakma
    if any(k in n for k in [
        "kardiyo", "cardio", "koşu", "hiit", "yağ yakma",
        "zayıflama", "kilo", "metabolik", "fat burn", "aerobik",
    ]):
        return "cut"
    # Atletizm / Fonksiyonel
    if any(k in n for k in [
        "atletizm", "athletic", "performans", "fonksiyonel",
        "functional", "crossfit", "çeviklik", "hız",
        "dayanıklılık", "kondisyon", "agility", "spor performans",
    ]):
        return "Athletics"
    # Şekillendirme / Sıkılaştırma
    if any(k in n for k in [
        "şekillen", "sculpt", "toning", "tone", "estetik",
        "sıkılaş", "fit", "vücut şekil", "formunu",
    ]):
        return "Muscle & Sculpting"
    # Bodybuilding / Kas yapma (geniş kapsam — varsayılan)
    if any(k in n for k in [
        "kas", "hipertrofi", "bodybuilding", "muscle", "hacim",
        "bulk", "vücut geliştirme", "split", "göğüs", "sırt",
        "omuz", "bacak", "kol", "bicep", "tricep", "bench",
        "antrenman", "egzersiz", "program", "workout",
    ]):
        return "Bodybuilding"
    return "Bodybuilding"   # Eşleşme yoksa Bodybuilding varsayılan


def _map_equipment(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ["dumbbell", "dambıl", "halter dambıl"]):
        return "Dumbbell Only"
    if any(k in n for k in [
        "ev", "home", "vücut ağırlığı", "bodyweight",
        "treadmill", "evde", "no equipment",
    ]):
        return "At Home"
    if any(k in n for k in ["kettlebell"]):
        return "Full Gym"
    if any(k in n for k in ["barbell", "bench", "squat rack", "halter bar"]):
        return "Full Gym"
    return "Full Gym"


def _estimate_time(ex_count: int) -> int:
    if ex_count <= 3:
        return 25
    if ex_count <= 5:
        return 40
    if ex_count <= 7:
        return 55
    return 70


def _build_programs(raw: list[dict]) -> list[dict]:
    """Ham dataset'i program listesine çevir."""
    programs = []
    seen_titles = set()
    for i, item in enumerate(raw):
        title = (item.get("program_adi") or "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        det  = item.get("program_detaylari") or {}
        exs  = det.get("egzersizler") or []
        hedef = det.get("hedef_kitle", "")
        programs.append({
            "id":               f"ds-{i}",
            "title":            title,
            "description":      f"{len(exs)} egzersizden oluşan {title.lower()} programı.",
            "level":            _map_level(hedef),
            "goal":             _map_goal(title),
            "equipment":        _map_equipment(title),
            "time_per_workout": _estimate_time(len(exs)),
            "program_length":   "8",
            "total_exercises":  len(exs),
            "_exercises":       exs,   # iç kullanım için
        })
    return programs


_RAW_DATASET = _load_dataset()
_ALL_PROGRAMS = _build_programs(_RAW_DATASET)

# Tüm egzersiz adları (suggest için)
_ALL_EXERCISE_NAMES: list[dict] = []
_seen_names: set = set()
for _p in _ALL_PROGRAMS:
    for _e in _p["_exercises"]:
        _nm = (_e.get("ad") or "").strip()
        if _nm and _nm not in _seen_names:
            _seen_names.add(_nm)
            _ALL_EXERCISE_NAMES.append({
                "name": _nm,
                "sets": _e.get("set") or 3,
                "reps": str(_e.get("tekrar") or "10-12"),
            })


# ── Set/Rep yapılandırmaları ──────────────────────────────────────────────────
_SETS_REPS: dict[str, tuple] = {
    "Bodybuilding":       (4, "8-12",  60),
    "Muscle & Sculpting": (3, "12-15", 45),
    "Athletics":          (3, "15-20", 45),
    "Powerbuilding":      (5, "3-5",   90),
    "cut":                (3, "12-15", 45),
    "bulk":               (4, "8-10",  75),
    "maintain":           (3, "10-12", 60),
}
_REST_BY_LEVEL: dict[str, int] = {
    "Beginner": 90, "Intermediate": 60, "Advanced": 45, "All Levels": 60,
}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/programs")
async def get_programs(
    goal:      Optional[str] = Query(None),
    level:     Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    max_time:  Optional[int] = Query(None),
    _user_id:  str           = Depends(get_current_user),
):
    """Dataset'ten program listesi döndür — filtre destekli."""
    results = [p for p in _ALL_PROGRAMS]  # kopya

    if goal:
        g = goal.lower()
        results = [p for p in results if g in p["goal"].lower()]
    if level:
        lv = level.lower()
        results = [p for p in results if lv in p["level"].lower()]
    if equipment:
        eq = equipment.lower()
        results = [p for p in results if eq in p["equipment"].lower()]
    if max_time:
        results = [p for p in results if p["time_per_workout"] <= max_time]

    # Sonuç yoksa tüm listeyi döndür (filtre seçilmemişse mantıklı fallback)
    if not results and not any([goal, level, equipment]):
        results = list(_ALL_PROGRAMS)

    results.sort(key=lambda p: p["title"])
    # _exercises alanını gizle
    clean = [{k: v for k, v in p.items() if k != "_exercises"} for p in results[:12]]
    return {"programs": clean}


@router.get("/suggest")
async def suggest_exercises(
    goal:      Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    level:     Optional[str] = Query(None),
    count:     int            = Query(8, ge=4, le=12),
    _user_id:  str            = Depends(get_current_user),
):
    """Dataset'ten hedef/ekipmana uygun rastgele egzersiz listesi döndür."""
    sets_n, reps_str, rest_default = _SETS_REPS.get(goal or "", (3, "10-12", 60))
    rest_sec = _REST_BY_LEVEL.get(level or "", rest_default)

    pool = list(_ALL_EXERCISE_NAMES)
    random.shuffle(pool)
    selected = pool[:count]

    exercises = [
        {
            "order":        i + 1,
            "wger_id":      i + 1,
            "name":         ex["name"],
            "muscle_group": "Genel",
            "sets":         sets_n,
            "reps":         reps_str,
            "rest_sec":     rest_sec,
            "tip":          "Kontrollü tempo ve doğru form uygulayın.",
            "images":       [],
            "videos":       [],
        }
        for i, ex in enumerate(selected)
    ]
    return {"exercises": exercises, "source": "dataset"}


def get_program_exercises(title: str, goal: str = "", level: str = "",
                          sets_override: int = None, rest_override: int = None) -> list[dict]:
    """
    Verilen program başlığına göre dataset'ten egzersizleri bul ve döndür.
    Dışarıdan çağrılabilir (ai.py generate_exercises kullanır).
    """
    # Başlık eşleşmesi bul
    match = None
    title_lower = title.lower().strip()
    for p in _ALL_PROGRAMS:
        if p["title"].lower() == title_lower:
            match = p
            break
    # Tam eşleşme yoksa kısmi ara
    if not match:
        for p in _ALL_PROGRAMS:
            if title_lower in p["title"].lower() or p["title"].lower() in title_lower:
                match = p
                break
    # Hâlâ bulunamazsa hedefe göre rastgele seç
    if not match:
        candidates = [p for p in _ALL_PROGRAMS if goal.lower() in p["goal"].lower()] or _ALL_PROGRAMS
        match = random.choice(candidates)

    prog_level = match.get("level", level or "Intermediate")
    sets_n, reps_str, rest_def = _SETS_REPS.get(
        match["goal"], _SETS_REPS.get(goal or "", (3, "10-12", 60))
    )
    rest_sec = rest_override or _REST_BY_LEVEL.get(prog_level, rest_def)
    if sets_override:
        sets_n = sets_override

    result = []
    for i, ex in enumerate(match["_exercises"]):
        name = (ex.get("ad") or "").strip()
        if not name:
            continue
        ex_sets = ex.get("set") or sets_n
        ex_reps = str(ex.get("tekrar") or reps_str)
        result.append({
            "order":        i + 1,
            "name":         name,
            "muscle_group": "Genel",
            "sets":         ex_sets,
            "reps":         ex_reps,
            "rest_sec":     rest_sec,
            "tip":          "Kontrollü tempo ve doğru form uygulayın.",
            "images":       [],
            "videos":       [],
        })
    return result


@router.get("/search")
async def search_exercises(
    term:     str = Query(..., min_length=2),
    _user_id: str = Depends(get_current_user),
):
    matches = [e for e in _ALL_EXERCISE_NAMES
               if term.lower() in e["name"].lower()][:20]
    return {"suggestions": [e["name"] for e in matches]}


@router.get("")
async def list_exercises(
    limit:    int = Query(20, le=100),
    offset:   int = Query(0),
    _user_id: str = Depends(get_current_user),
):
    page = _ALL_EXERCISE_NAMES[offset: offset + limit]
    return {"results": [{"id": i + offset + 1, "name": e["name"]} for i, e in enumerate(page)]}


@router.get("/categories")
async def get_categories(_user_id: str = Depends(get_current_user)):
    return {"results": [{"id": 8, "name": "Arms"}, {"id": 9, "name": "Legs"},
                        {"id": 10, "name": "Chest"}, {"id": 11, "name": "Back"},
                        {"id": 12, "name": "Shoulders"}, {"id": 13, "name": "Cardio"}]}


@router.get("/muscles")
async def get_muscles(_user_id: str = Depends(get_current_user)):
    return {"results": [{"id": 1, "name": "Biceps"}, {"id": 2, "name": "Quadriceps"},
                        {"id": 3, "name": "Chest"}, {"id": 4, "name": "Back"}]}


@router.get("/equipment")
async def get_equipment(_user_id: str = Depends(get_current_user)):
    return {"results": [{"id": 1, "name": "Barbell"}, {"id": 3, "name": "Dumbbell"},
                        {"id": 7, "name": "Kettlebell"}, {"id": 8, "name": "Bodyweight"}]}


@router.get("/images")
async def get_images(_user_id: str = Depends(get_current_user)):
    return {"results": []}


@router.get("/{exercise_id}")
async def get_exercise_detail(exercise_id: int, _user_id: str = Depends(get_current_user)):
    if exercise_id <= len(_ALL_EXERCISE_NAMES):
        ex = _ALL_EXERCISE_NAMES[exercise_id - 1]
        return {"id": exercise_id, "name": ex["name"], "description": "",
                "category": {"name": "Genel"}, "muscles": [], "equipment": [],
                "images": [], "videos": []}
    return {"id": exercise_id, "name": f"Egzersiz {exercise_id}",
            "description": "", "category": {"name": "Genel"},
            "muscles": [], "equipment": [], "images": [], "videos": []}

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import asyncio
import re
import json
import logging
import os
import httpx
from config import settings
from db.supabase import supabase_admin
from models.schemas import ChatRequest, ChatResponse
from utils.auth import get_current_user
from datetime import date
from routers.exercises import get_program_exercises
from utils.openfoodfacts import search_foods

_logger = logging.getLogger(__name__)

# ─── Öğün dağılımı (sabit) ───────────────────────────────────────────────────
_MEAL_DIST: dict[str, list[dict]] = {
    "3": [
        {"type": "breakfast", "name_tr": "Kahvaltı",     "time": "08:00", "ratio": 0.30},
        {"type": "lunch",     "name_tr": "Öğle Yemeği",  "time": "13:00", "ratio": 0.40},
        {"type": "dinner",    "name_tr": "Akşam Yemeği", "time": "19:00", "ratio": 0.30},
    ],
    "4": [
        {"type": "breakfast", "name_tr": "Kahvaltı",     "time": "08:00", "ratio": 0.25},
        {"type": "snack",     "name_tr": "Ara Öğün",     "time": "11:00", "ratio": 0.15},
        {"type": "lunch",     "name_tr": "Öğle Yemeği",  "time": "13:00", "ratio": 0.35},
        {"type": "dinner",    "name_tr": "Akşam Yemeği", "time": "19:00", "ratio": 0.25},
    ],
    "5": [
        {"type": "breakfast", "name_tr": "Kahvaltı",     "time": "07:30", "ratio": 0.25},
        {"type": "snack",     "name_tr": "Sabah Arası",  "time": "10:30", "ratio": 0.10},
        {"type": "lunch",     "name_tr": "Öğle Yemeği",  "time": "13:00", "ratio": 0.30},
        {"type": "snack",     "name_tr": "İkindi Arası", "time": "16:00", "ratio": 0.10},
        {"type": "dinner",    "name_tr": "Akşam Yemeği", "time": "19:30", "ratio": 0.25},
    ],
}

# ─── Öğün × diyet/hedef anahtar kelime havuzu ────────────────────────────────
# Her giriş için 5-6 kelime: Türkçe + İngilizce (OFF world için fallback)
_MEAL_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "breakfast": {
        "cut":          ["yumurta", "yulaf ezmesi", "süzme yoğurt", "oatmeal", "eggs", "greek yogurt"],
        "bulk":         ["granola", "yulaf ezmesi", "fıstık ezmesi", "oatmeal", "peanut butter", "banana"],
        "maintain":     ["yulaf ezmesi", "yumurta", "muz", "oat", "granola", "yogurt"],
        "balanced":     ["yulaf ezmesi", "yumurta", "muz", "oat", "granola", "yogurt"],
        "high_protein": ["yumurta", "lor peyniri", "yoğurt", "eggs", "cottage cheese", "greek yogurt"],
        "low_carb":     ["yumurta", "beyaz peynir", "avokado", "eggs", "cheese", "avocado"],
        "vegetarian":   ["yulaf ezmesi", "yoğurt", "ceviz", "granola", "oat", "walnut"],
        "vegan":        ["yulaf ezmesi", "muz", "badem", "oat", "banana", "almond"],
    },
    "lunch": {
        "cut":          ["tavuk göğsü", "mercimek", "brokoli", "chicken breast", "lentil", "broccoli"],
        "bulk":         ["tavuk göğsü", "pirinç", "nohut", "chicken", "rice", "chickpea"],
        "maintain":     ["tavuk", "bulgur", "salata", "chicken", "quinoa", "rice"],
        "balanced":     ["tavuk", "bulgur", "sebze", "chicken", "rice", "vegetable"],
        "high_protein": ["tavuk göğsü", "ton balığı", "yumurta", "chicken breast", "tuna", "eggs"],
        "low_carb":     ["tavuk", "brokoli", "roka", "chicken", "broccoli", "salad"],
        "vegetarian":   ["mercimek", "nohut", "beyaz peynir", "lentil", "chickpea", "feta"],
        "vegan":        ["mercimek", "tofu", "kinoa", "lentil", "quinoa", "chickpea"],
    },
    "dinner": {
        "cut":          ["somon", "tavuk", "brokoli", "salmon", "chicken breast", "broccoli"],
        "bulk":         ["dana kıyma", "makarna", "pirinç", "pasta", "rice", "beef"],
        "maintain":     ["somon", "bulgur", "sebze", "salmon", "fish", "chicken"],
        "balanced":     ["somon", "sebze", "bulgur", "salmon", "chicken", "rice"],
        "high_protein": ["somon", "dana eti", "tavuk göğsü", "salmon", "beef", "chicken"],
        "low_carb":     ["somon", "kabak", "brokoli", "salmon", "zucchini", "broccoli"],
        "vegetarian":   ["nohut", "bulgur", "beyaz peynir", "chickpea", "lentil", "feta"],
        "vegan":        ["mercimek", "kinoa", "tofu", "lentil", "quinoa", "tempeh"],
    },
    "snack": {
        "cut":          ["badem", "süzme yoğurt", "ceviz", "almond", "greek yogurt", "yogurt"],
        "bulk":         ["fıstık ezmesi", "muz", "granola", "peanut butter", "banana", "almond"],
        "maintain":     ["badem", "muz", "yoğurt", "almond", "banana", "yogurt"],
        "balanced":     ["badem", "muz", "yoğurt", "almond", "banana", "granola"],
        "high_protein": ["süzme yoğurt", "beyaz peynir", "yoğurt", "greek yogurt", "cottage cheese", "protein"],
        "low_carb":     ["badem", "ceviz", "fındık", "almond", "walnut", "pecan"],
        "vegetarian":   ["yoğurt", "elma", "badem", "yogurt", "apple", "walnut"],
        "vegan":        ["badem", "muz", "ceviz", "almond", "banana", "dates"],
    },
}

router = APIRouter(prefix="/api/ai", tags=["ai"])

SYSTEM_PROMPT = """Sen FitTrack AI'nın kişisel fitness koçusun. Türkçe konuşuyorsun.
Kullanıcının günlük kalori, antrenman ve beslenme verilerine erişimin var.
Yanıtların kısa, pratik ve motive edici olmalı. Tıbbi tavsiye vermekten kaçın."""


async def _groq_chat(messages: list[dict]) -> str:
    """Groq API'ye istek at, yanıtı döndür. Başarısız olursa HTTPException fırlat."""
    if not settings.grok_api_key:
        raise HTTPException(status_code=503, detail="Groq API key yapılandırılmamış.")
    headers = {
        "Authorization": f"Bearer {settings.grok_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.grok_model,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(settings.grok_endpoint, json=payload, headers=headers)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Groq API hatası: {r.text[:200]}")
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


async def build_user_context(user_id: str) -> tuple[str, list[str]]:
    """Kullanıcı profili + bugünün verilerini bağlam olarak hazırla."""
    context_parts = []
    today = date.today().isoformat()

    # Profil
    profile_res = (
        supabase_admin.table("profiles")
        .select("full_name,age,weight_kg,goal,calorie_target,protein_target")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if profile_res.data:
        p = profile_res.data[0]
        goal_map = {"cut": "Yağ yakma", "bulk": "Kas yapma", "maintain": "Form koruma"}
        context_parts.append(
            f"Kullanıcı: {p.get('full_name')}, {p.get('age')} yaş, {p.get('weight_kg')} kg. "
            f"Hedef: {goal_map.get(p.get('goal',''), p.get('goal',''))}. "
            f"Günlük kalori hedefi: {p.get('calorie_target')} kcal, "
            f"protein hedefi: {p.get('protein_target')} g."
        )

    # Bugünkü öğünler
    meal_res = (
        supabase_admin.table("meals")
        .select("calories,protein,carb,fat,meal_type")
        .eq("user_id", user_id)
        .eq("date", today)
        .execute()
    )
    if meal_res.data:
        total_cal  = sum(r.get("calories", 0) for r in meal_res.data)
        total_prot = sum(r.get("protein",  0) for r in meal_res.data)
        context_parts.append(
            f"Bugün alınan: {round(total_cal)} kcal, {round(total_prot)} g protein."
        )

    # Son antrenman
    workout_res = (
        supabase_admin.table("workouts")
        .select("date,duration_min,programs(title)")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if workout_res.data:
        w = workout_res.data[0]
        prog_title = (w.get("programs") or {}).get("title", "Serbest antrenman")
        context_parts.append(
            f"Son antrenman: {w.get('date')} tarihinde {prog_title}, "
            f"{w.get('duration_min', '?')} dakika."
        )

    context_str = "\n".join(context_parts)
    return context_str, context_parts


@router.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest, user_id: str = Depends(get_current_user)):
    context_str, context_parts = await build_user_context(user_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context_str:
        messages.append({
            "role": "system",
            "content": f"[Kullanıcı bağlamı]\n{context_str}",
        })
    for msg in data.history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": data.message})

    reply = await _groq_chat(messages)
    return ChatResponse(reply=reply, context_used=context_parts)


@router.get("/daily-tip")
async def daily_tip(user_id: str = Depends(get_current_user)):
    """Anasayfa için kısa günlük AI antrenör notu."""
    context_str, _ = await build_user_context(user_id)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"[Kullanıcı bağlamı]\n{context_str}"},
        {
            "role": "user",
            "content": (
                "Kullanıcının bugünkü verilerine bakarak 2-3 cümlelik, "
                "pratik ve motive edici bir antrenör notu yaz. Türkçe, kısa tut."
            ),
        },
    ]

    tip = await _groq_chat(messages)
    return {"tip": tip}


# ─── Program Egzersiz Listesi ─────────────────────────────────────────────────

@router.post("/generate-exercises")
async def generate_exercises(
    user_id:      str = Depends(get_current_user),
    title:        str = Query(...),
    goal:         Optional[str] = Query(None),
    equipment:    Optional[str] = Query(None),
    duration_min: Optional[int] = Query(None),
    level:        Optional[str] = Query(None),
):
    """Seçilen programın bilgisine göre egzersiz listesi üret (yerel dataset)."""
    def clean_list_str(s: str) -> str:
        if not s:
            return ""
        items = re.findall(r"'([^']+)'", s)
        return items[0] if items else re.sub(r"[\[\]'\"\\]", "", s).split(",")[0].strip()

    safe_title = re.sub(r'[^\w\s\-&.,()İÇŞĞÜÖıçşğüö]', ' ', title).strip()[:120]
    safe_goal  = clean_list_str(goal  or "") or "Genel fitness"
    safe_level = clean_list_str(level or "") or "Orta"

    exercises = get_program_exercises(
        title=safe_title,
        goal=safe_goal,
        level=safe_level,
    )
    return {"exercises": exercises}


# ─── Garantili fallback besin listesi (100g başına değerler) ─────────────────
_FALLBACK_FOODS: dict[str, list[dict]] = {
    "breakfast": [
        {"name_tr": "Yulaf Ezmesi",     "calories": 389, "protein": 17.0, "carbohydrate": 66.0, "fat": 7.0,  "fiber": 10.0},
        {"name_tr": "Yumurta",          "calories": 155, "protein": 13.0, "carbohydrate": 1.1,  "fat": 11.0, "fiber": 0},
        {"name_tr": "Süzme Yoğurt",     "calories": 97,  "protein": 9.0,  "carbohydrate": 4.0,  "fat": 5.0,  "fiber": 0},
        {"name_tr": "Muz",              "calories": 89,  "protein": 1.1,  "carbohydrate": 23.0, "fat": 0.3,  "fiber": 2.6},
        {"name_tr": "Tam Buğday Ekmek", "calories": 247, "protein": 9.0,  "carbohydrate": 41.0, "fat": 3.0,  "fiber": 7.0},
    ],
    "lunch": [
        {"name_tr": "Tavuk Göğsü", "calories": 165, "protein": 31.0, "carbohydrate": 0,    "fat": 3.6,  "fiber": 0},
        {"name_tr": "Bulgur",      "calories": 342, "protein": 12.0, "carbohydrate": 76.0, "fat": 1.3,  "fiber": 18.0},
        {"name_tr": "Mercimek",    "calories": 116, "protein": 9.0,  "carbohydrate": 20.0, "fat": 0.4,  "fiber": 8.0},
        {"name_tr": "Nohut",       "calories": 164, "protein": 8.9,  "carbohydrate": 27.0, "fat": 2.6,  "fiber": 7.6},
        {"name_tr": "Pirinç",      "calories": 130, "protein": 2.7,  "carbohydrate": 28.0, "fat": 0.3,  "fiber": 0.4},
    ],
    "dinner": [
        {"name_tr": "Somon",       "calories": 208, "protein": 20.0, "carbohydrate": 0,    "fat": 13.0, "fiber": 0},
        {"name_tr": "Tavuk Göğsü", "calories": 165, "protein": 31.0, "carbohydrate": 0,    "fat": 3.6,  "fiber": 0},
        {"name_tr": "Brokoli",     "calories": 34,  "protein": 2.8,  "carbohydrate": 7.0,  "fat": 0.4,  "fiber": 2.6},
        {"name_tr": "Makarna",     "calories": 371, "protein": 13.0, "carbohydrate": 74.0, "fat": 1.5,  "fiber": 2.7},
        {"name_tr": "Dana Eti",    "calories": 250, "protein": 26.0, "carbohydrate": 0,    "fat": 15.0, "fiber": 0},
    ],
    "snack": [
        {"name_tr": "Badem",         "calories": 579, "protein": 21.0, "carbohydrate": 22.0, "fat": 50.0, "fiber": 12.5},
        {"name_tr": "Ceviz",         "calories": 654, "protein": 15.0, "carbohydrate": 14.0, "fat": 65.0, "fiber": 6.7},
        {"name_tr": "Yoğurt",        "calories": 97,  "protein": 9.0,  "carbohydrate": 4.0,  "fat": 5.0,  "fiber": 0},
        {"name_tr": "Muz",           "calories": 89,  "protein": 1.1,  "carbohydrate": 23.0, "fat": 0.3,  "fiber": 2.6},
        {"name_tr": "Fıstık Ezmesi", "calories": 588, "protein": 25.0, "carbohydrate": 20.0, "fat": 50.0, "fiber": 6.0},
    ],
}

# ─── Beslenme Planı (Open Food Facts API) ────────────────────────────────────

async def _search_for_meal(keywords: list[str], n_items: int, meal_type: str = "snack") -> list[dict]:
    """
    Tüm anahtar kelimeleri paralel sorgular.
    1. Geçiş: resim + kalori olan sonuçlar (tercihli)
    2. Geçiş: yetmezse sadece kalori olan sonuçlar da kabul edilir
    """
    tasks = [search_foods(kw, max_results=8) for kw in keywords]
    grouped = await asyncio.gather(*tasks, return_exceptions=True)

    seen: set[str] = set()
    with_img: list[dict] = []
    no_img: list[dict] = []

    for batch in grouped:
        if isinstance(batch, Exception):
            continue
        for r in batch:
            if not (r.get("calories") or 0):
                continue
            key = (r.get("name_tr") or r.get("name", "")).lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            if (r.get("image_url") or "").startswith("http"):
                with_img.append(r)
            else:
                no_img.append(r)

    combined = with_img + no_img

    # API yeterli sonuç vermediyse garantili fallback listesiyle tamamla
    if len(combined) < n_items:
        fallback_pool = _FALLBACK_FOODS.get(meal_type, _FALLBACK_FOODS["snack"])
        for fb in fallback_pool:
            if len(combined) >= n_items:
                break
            key = fb["name_tr"].lower()
            if key not in seen:
                seen.add(key)
                combined.append({"id": 0, "image_url": "", **fb})

    return combined[:n_items]


def _build_items_from_api(foods: list[dict], cal_target: int) -> list[dict]:
    """Open Food Facts sonuçlarından porsiyonlu besin listesi oluştur."""
    items: list[dict] = []
    n = len(foods)
    remaining = cal_target

    for i, food in enumerate(foods):
        cal100 = food.get("calories") or 0
        if cal100 <= 0:
            continue
        share    = remaining / max(1, n - i)
        ideal_g  = round((share / cal100) * 100)
        # Kalorisi yoğun besinler (≥400 kcal/100g): max 200g; hafif besinler: max 500g
        max_g    = 200 if cal100 >= 400 else 500
        amount_g = max(15, min(max_g, ideal_g))
        ratio    = amount_g / 100

        items.append({
            "food_id":   food.get("id", 0),
            "food":      food.get("name_tr") or food.get("name", "?"),
            "amount_g":  amount_g,
            "amount":    f"{amount_g} g",
            "calories":  round(cal100 * ratio, 1),
            "protein":   round((food.get("protein")      or 0) * ratio, 1),
            "carb":      round((food.get("carbohydrate") or 0) * ratio, 1),
            "fat":       round((food.get("fat")          or 0) * ratio, 1),
            "fiber":     round((food.get("fiber")        or 0) * ratio, 1),
            "image_url": food.get("image_url") or "",
        })
        remaining -= round(cal100 * ratio)

    return items


@router.post("/generate-meal-plan")
async def generate_meal_plan(
    user_id:       str = Depends(get_current_user),
    goal:          Optional[str] = Query(None),
    diet:          Optional[str] = Query(None),
    meals_per_day: Optional[int] = Query(None),
):
    # Profil al
    profile_res = (
        supabase_admin.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    )
    p = profile_res.data[0] if profile_res.data else {}

    goal        = goal or p.get("goal", "maintain")
    diet        = diet or p.get("diet_preference", "balanced")
    n_meals     = min(max(meals_per_day or 3, 3), 5)
    cal_target  = int(p.get("calorie_target") or 2000)
    prot_target = int(p.get("protein_target") or 150)
    carb_target = int(p.get("carb_target")    or 200)
    fat_target  = int(p.get("fat_target")     or 65)

    if goal != p.get("goal"):
        if goal == "cut":
            cal_target = max(1200, cal_target - 300)
        elif goal == "bulk":
            cal_target = cal_target + 300

    meal_dist = _MEAL_DIST.get(str(n_meals), _MEAL_DIST["3"])

    # Her öğün için anahtar kelime havuzu
    def _keywords(mtype: str) -> list[str]:
        pool = _MEAL_KEYWORDS.get(mtype, {})
        return pool.get(diet) or pool.get(goal) or pool.get("balanced", ["yulaf", "tavuk", "salata"])

    # Tüm öğün aramalarını paralel yap
    n_items_list = [2 if s["type"] == "snack" else 3 for s in meal_dist]
    search_tasks = [
        _search_for_meal(_keywords(s["type"]), n_items_list[i], s["type"])
        for i, s in enumerate(meal_dist)
    ]
    foods_per_slot = await asyncio.gather(*search_tasks, return_exceptions=True)

    meals: list[dict] = []
    total_cal = total_prot = total_carb = total_fat = 0.0

    for idx, slot in enumerate(meal_dist):
        meal_cal = round(cal_target * slot["ratio"])
        foods = foods_per_slot[idx]
        if isinstance(foods, Exception) or not foods:
            foods = []

        items = _build_items_from_api(foods, meal_cal)

        mc = round(sum(i["calories"] for i in items), 1)
        mp = round(sum(i["protein"]  for i in items), 1)
        mk = round(sum(i["carb"]     for i in items), 1)
        my = round(sum(i["fat"]      for i in items), 1)
        total_cal += mc; total_prot += mp; total_carb += mk; total_fat += my

        meals.append({
            "type":           slot["type"],
            "name_tr":        slot["name_tr"],
            "time":           slot["time"],
            "total_calories": mc,
            "total_protein":  mp,
            "total_carb":     mk,
            "total_fat":      my,
            "items":          items,
        })

    return {
        "goal":           goal,
        "diet":           diet,
        "ai_generated":   True,
        "total_calories": round(total_cal),
        "total_protein":  round(total_prot, 1),
        "total_carb":     round(total_carb, 1),
        "total_fat":      round(total_fat,  1),
        "targets": {
            "calories": cal_target,
            "protein":  prot_target,
            "carb":     carb_target,
            "fat":      fat_target,
        },
        "meals": meals,
    }

from fastapi import APIRouter, HTTPException, Query, Depends
from db.supabase import supabase_admin
from models.schemas import MealCreate, MealResponse
from utils.auth import get_current_user
from datetime import date


async def _fetch_food(food_id) -> dict:
    """Besin verilerini Supabase'den al. Bulunamazsa boş dict döner."""
    if food_id is None:
        return {}
    try:
        res = (
            supabase_admin.table("foods")
            .select("name,name_tr,calories,protein,carbohydrate,fat")
            .eq("id", food_id)
            .single()
            .execute()
        )
        return res.data or {}
    except Exception:
        return {}

router = APIRouter(prefix="/api/meals", tags=["meals"])


def calc_macros(food: dict, amount_g: float) -> dict:
    """100g baz alınarak porsiyon makrolarını hesapla."""
    ratio = amount_g / 100
    return {
        "calories": round((food.get("calories") or 0) * ratio, 1),
        "protein":  round((food.get("protein")   or 0) * ratio, 1),
        "carb":     round((food.get("carbohydrate") or 0) * ratio, 1),
        "fat":      round((food.get("fat")        or 0) * ratio, 1),
    }


@router.get("", response_model=list[MealResponse])
async def get_meals(
    target_date: date = Query(..., alias="date"),
    user_id: str = Depends(get_current_user),
):
    res = (
        supabase_admin.table("meals")
        .select("*, foods(name, name_tr)")
        .eq("user_id", user_id)
        .eq("date", target_date.isoformat())
        .order("meal_type")
        .execute()
    )
    meals = []
    for row in res.data or []:
        food_info = row.pop("foods", {}) or {}
        # DB'deki food_name_tr öncelikli, yoksa JOIN'den al
        row["food_name"]    = row.get("food_name_tr") or food_info.get("name")
        row["food_name_tr"] = row.get("food_name_tr") or food_info.get("name_tr")
        meals.append(MealResponse(**row))
    return meals


@router.post("", response_model=MealResponse, status_code=201)
async def add_meal(data: MealCreate, user_id: str = Depends(get_current_user)):
    food = await _fetch_food(data.food_id)

    if food:
        macros    = calc_macros(food, data.amount_g)
        food_name    = food.get("name")
        food_name_tr = food.get("name_tr")
    elif data.calories_inline is not None:
        # Besin DB'de yok ama inline veri var — doğrudan kullan
        macros = {
            "calories": round(data.calories_inline, 1),
            "protein":  round(data.protein_inline or 0, 1),
            "carb":     round(data.carb_inline    or 0, 1),
            "fat":      round(data.fat_inline     or 0, 1),
        }
        food_name    = data.food_name
        food_name_tr = data.food_name
    else:
        raise HTTPException(status_code=404, detail="Besin bulunamadı ve inline veri sağlanmadı")

    payload = {
        "user_id":       user_id,
        "date":          data.date.isoformat(),
        "meal_type":     data.meal_type,
        "food_id":       data.food_id,
        "amount_g":      data.amount_g,
        "food_name_tr":  food_name_tr or food_name,
        **macros,
    }
    if data.image_url:
        payload["image_url"] = data.image_url

    try:
        res = supabase_admin.table("meals").insert(payload).execute()
    except Exception as e:
        err_str = str(e)
        # FK ihlali (food_id Supabase'de yok) → food_id olmadan tekrar dene
        if "23503" in err_str or "food_id" in err_str:
            payload.pop("food_id", None)
        # image_url kolonu henüz eklenmemişse onu da çıkar
        if "image_url" in err_str or "42703" in err_str:
            payload.pop("image_url", None)
        res = supabase_admin.table("meals").insert(payload).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Öğün eklenemedi")

    row = res.data[0]
    row["food_name"]    = food_name
    row["food_name_tr"] = food_name_tr
    return MealResponse(**row)


@router.delete("/{meal_id}", status_code=204)
async def delete_meal(meal_id: str, user_id: str = Depends(get_current_user)):
    res = (
        supabase_admin.table("meals")
        .delete()
        .eq("id", meal_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Öğün bulunamadı")


@router.get("/summary", tags=["meals"])
async def daily_summary(
    target_date: date = Query(..., alias="date"),
    user_id: str = Depends(get_current_user),
):
    """Günlük toplam kalori ve makro özeti."""
    res = (
        supabase_admin.table("meals")
        .select("calories,protein,carb,fat")
        .eq("user_id", user_id)
        .eq("date", target_date.isoformat())
        .execute()
    )
    totals = {"calories": 0.0, "protein": 0.0, "carb": 0.0, "fat": 0.0}
    for row in res.data or []:
        for key in totals:
            totals[key] += row.get(key) or 0
    return {k: round(v, 1) for k, v in totals.items()}

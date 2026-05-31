from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.supabase import supabase_admin
from models.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from utils.auth import get_current_user
import math

router = APIRouter(prefix="/api/user", tags=["user"])
security = HTTPBearer()


def calculate_targets(weight_kg: float, height_cm: float, age: int,
                       gender: str, activity_level: str, goal: str) -> dict:
    """Harris-Benedict + TDEE ile makro hedefleri hesapla."""
    if gender == "male":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

    multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9
    }
    tdee = bmr * multipliers.get(activity_level, 1.55)

    calories = tdee - 400 if goal == "cut" else tdee + 300 if goal == "bulk" else tdee
    protein  = weight_kg * 2.0
    fat      = (calories * 0.25) / 9
    carb     = (calories - protein * 4 - fat * 9) / 4

    return {
        "calorie_target": math.ceil(calories),
        "protein_target": math.ceil(protein),
        "fat_target":     math.ceil(fat),
        "carb_target":    math.ceil(carb),
    }


@router.post("/profile", response_model=ProfileResponse)
async def create_profile(data: ProfileCreate, user_id: str = Depends(get_current_user)):
    targets = calculate_targets(
        data.weight_kg, data.height_cm, data.age,
        data.gender, data.activity_level, data.goal
    )
    payload = {
        "id": user_id,
        **data.model_dump(),
        **targets,
    }
    res = supabase_admin.table("profiles").upsert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Profil kaydedilemedi")
    return ProfileResponse(**res.data[0])


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user)):
    try:
        res = supabase_admin.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    except Exception:
        raise HTTPException(status_code=500, detail="Profil sorgulanamadı")
    if not res.data:
        raise HTTPException(status_code=404, detail="Profil bulunamadı")
    return ProfileResponse(**res.data[0])


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(data: ProfileUpdate, user_id: str = Depends(get_current_user)):
    updates = data.model_dump(exclude_none=True)

    # Mevcut profili çek (varsa)
    try:
        current_res = (
            supabase_admin.table("profiles")
            .select("*").eq("id", user_id).limit(1).execute()
        )
        current_data = current_res.data[0] if current_res.data else {}
    except Exception:
        current_data = {}

    # Makro hesaplaması için birleştirilmiş profil
    if "goal" in updates or "activity_level" in updates or "weight_kg" in updates or not current_data:
        merged = {
            "weight_kg":    75, "height_cm": 175, "age": 25,
            "gender":       "male", "activity_level": "moderate", "goal": "maintain",
            **current_data, **updates,
        }
        targets = calculate_targets(
            float(merged["weight_kg"]), float(merged["height_cm"]),
            int(merged["age"]),  merged["gender"],
            merged.get("activity_level", "moderate"),
            merged.get("goal", "maintain"),
        )
        updates.update(targets)

    # Profil yoksa oluştur, varsa güncelle (upsert)
    payload = {"id": user_id, **updates}
    if not current_data:
        # Zorunlu alanları varsayılanla doldur
        payload.setdefault("full_name",  updates.get("full_name", "Kullanıcı"))
        payload.setdefault("gender",     "male")
        payload.setdefault("age",        25)
        payload.setdefault("height_cm",  175)
        payload.setdefault("weight_kg",  75)
        payload.setdefault("goal",       "maintain")

    res = supabase_admin.table("profiles").upsert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Güncelleme başarısız")
    return ProfileResponse(**res.data[0])

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.supabase import supabase, supabase_admin
from models.schemas import RegisterRequest, LoginRequest, TokenResponse
from utils.auth import verify_token
import math
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

def calculate_targets(weight_kg: float, height_cm: float, age: int,
                       gender: str, activity_level: str, goal: str) -> dict:
    """Harris-Benedict formülü ile günlük makro hedefleri hesapla."""
    if gender == "male":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

    activity_multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)

    if goal == "cut":
        calories = tdee - 400
    elif goal == "bulk":
        calories = tdee + 300
    else:
        calories = tdee

    protein = weight_kg * 2.0          # 2g/kg
    fat = (calories * 0.25) / 9        # kalorilerin %25'i
    carb = (calories - protein * 4 - fat * 9) / 4

    return {
        "calorie_target": math.ceil(calories),
        "protein_target": math.ceil(protein),
        "fat_target": math.ceil(fat),
        "carb_target": math.ceil(carb),
    }


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest):
    try:
        res = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })
        if res.user is None:
            logger.warning("Supabase sign_up returned no user: %s", res)
            raise HTTPException(status_code=400, detail="Kayıt başarısız")

        if res.session is None:
            raise HTTPException(
                status_code=400,
                detail="E-posta doğrulaması gerekiyor. Lütfen e-postanı kontrol et.",
            )

        return TokenResponse(
            access_token=res.session.access_token,
            user_id=res.user.id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Register failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })
        if res.user is None:
            raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")

        return TokenResponse(
            access_token=res.session.access_token,
            user_id=res.user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    supabase.auth.sign_out()
    return {"message": "Çıkış yapıldı"}

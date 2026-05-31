from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import date, datetime

# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

# ─── Profile ─────────────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    full_name: str
    gender: Literal["male", "female", "other"]
    age: int
    height_cm: float
    weight_kg: float
    goal: Literal["cut", "bulk", "maintain"]
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = "moderate"
    weekly_workout_days: int = 4
    diet_preference: str = "balanced"

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    goal: Optional[Literal["cut", "bulk", "maintain"]] = None
    activity_level: Optional[str] = None
    weekly_workout_days: Optional[int] = None
    diet_preference: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    full_name: str
    gender: str
    age: int
    height_cm: float
    weight_kg: float
    goal: str
    calorie_target: Optional[int] = None
    protein_target: Optional[int] = None
    carb_target: Optional[int] = None
    fat_target: Optional[int] = None
    weekly_workout_days: int
    diet_preference: str

# ─── Food ────────────────────────────────────────────────────────────────────

class FoodResponse(BaseModel):
    id: int
    name: str
    name_tr: Optional[str] = None
    serving_size: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbohydrate: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugars: Optional[float] = None
    image_url: Optional[str] = None

# ─── Meals ───────────────────────────────────────────────────────────────────

class MealCreate(BaseModel):
    date: date
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    food_id: Optional[int] = None
    amount_g: float
    # Inline beslenme verisi — food_id yoksa veya DB'de bulunmazsa kullanılır
    food_name: Optional[str] = None
    calories_inline: Optional[float] = None
    protein_inline: Optional[float] = None
    carb_inline: Optional[float] = None
    fat_inline: Optional[float] = None
    image_url: Optional[str] = None

class MealResponse(BaseModel):
    id: str
    date: date
    meal_type: str
    food_name: Optional[str] = None
    food_name_tr: Optional[str] = None
    amount_g: float
    calories: float
    protein: float
    carb: float
    fat: float
    image_url: Optional[str] = None

# ─── Workout ─────────────────────────────────────────────────────────────────

class WorkoutCreate(BaseModel):
    program_id: Optional[str] = None
    date: date
    duration_min: Optional[int] = None
    notes: Optional[str] = None

class SetCreate(BaseModel):
    workout_id: str
    exercise_name: str
    set_number: int
    reps: int
    weight_kg: float

class WorkoutResponse(BaseModel):
    id: str
    date: date
    duration_min: Optional[int] = None
    program_title: Optional[str] = None
    total_sets: int = 0
    notes: Optional[str] = None

# ─── Body Metrics ─────────────────────────────────────────────────────────────

class BodyMetricCreate(BaseModel):
    date: date
    weight_kg: float
    body_fat_pct: Optional[float] = None
    muscle_pct: Optional[float] = None
    waist_cm: Optional[float] = None

# ─── AI Chat ─────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str
    context_used: list[str] = []

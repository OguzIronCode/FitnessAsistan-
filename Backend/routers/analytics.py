from fastapi import APIRouter, Query, Depends
from db.supabase import supabase_admin
from utils.auth import get_current_user
from datetime import date, timedelta

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def get_summary(user_id: str = Depends(get_current_user)):
    """Dashboard için: bugünün istatistikleri + haftalık performans."""
    today = date.today()
    week_ago = today - timedelta(days=6)

    # Bugünkü öğün özeti
    meal_res = (
        supabase_admin.table("meals")
        .select("calories,protein,carb,fat")
        .eq("user_id", user_id)
        .eq("date", today.isoformat())
        .execute()
    )
    today_calories = sum(r.get("calories", 0) for r in (meal_res.data or []))
    today_protein  = sum(r.get("protein",  0) for r in (meal_res.data or []))
    today_carb     = sum(r.get("carb",     0) for r in (meal_res.data or []))
    today_fat      = sum(r.get("fat",      0) for r in (meal_res.data or []))

    # Bu haftaki antrenman sayısı
    workout_res = (
        supabase_admin.table("workouts")
        .select("id,duration_min,date")
        .eq("user_id", user_id)
        .gte("date", week_ago.isoformat())
        .execute()
    )
    weekly_workouts = workout_res.data or []

    # Son body metric
    body_res = (
        supabase_admin.table("body_metrics")
        .select("weight_kg,body_fat_pct,muscle_pct")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    latest_body = body_res.data[0] if body_res.data else {}

    # Kullanıcı hedef makroları
    try:
        profile_res = (
            supabase_admin.table("profiles")
            .select("calorie_target,protein_target,carb_target,fat_target")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        targets = profile_res.data[0] if profile_res.data else {}
    except Exception:
        targets = {}

    return {
        "today": {
            "calories":        round(today_calories, 1),
            "calorie_target":  targets.get("calorie_target", 2400),
            "protein":         round(today_protein, 1),
            "protein_target":  targets.get("protein_target", 150),
            "carb":            round(today_carb, 1),
            "carb_target":     targets.get("carb_target", 200),
            "fat":             round(today_fat, 1),
            "fat_target":      targets.get("fat_target", 65),
        },
        "weekly": {
            "workout_count":   len(weekly_workouts),
            "total_duration":  sum(w.get("duration_min") or 0 for w in weekly_workouts),
            "days":            [w["date"] for w in weekly_workouts],
        },
        "body":   latest_body,
    }


@router.get("/weekly-performance")
async def weekly_performance(
    days: int = Query(7, le=30),
    user_id: str = Depends(get_current_user),
):
    """Son N gün için günlük kalori + antrenman süresi."""
    today = date.today()
    since = today - timedelta(days=days - 1)

    meal_res = (
        supabase_admin.table("meals")
        .select("date,calories")
        .eq("user_id", user_id)
        .gte("date", since.isoformat())
        .execute()
    )
    workout_res = (
        supabase_admin.table("workouts")
        .select("date,duration_min")
        .eq("user_id", user_id)
        .gte("date", since.isoformat())
        .execute()
    )

    # Günlük topla
    cal_by_day: dict = {}
    dur_by_day: dict = {}

    for row in meal_res.data or []:
        d = row["date"]
        cal_by_day[d] = cal_by_day.get(d, 0) + (row.get("calories") or 0)

    for row in workout_res.data or []:
        d = row["date"]
        dur_by_day[d] = dur_by_day.get(d, 0) + (row.get("duration_min") or 0)

    result = []
    for i in range(days):
        d = (since + timedelta(days=i)).isoformat()
        result.append({
            "date": d,
            "calories": round(cal_by_day.get(d, 0), 1),
            "workout_minutes": dur_by_day.get(d, 0),
        })
    return result


@router.get("/personal-records")
async def personal_records(user_id: str = Depends(get_current_user)):
    """Egzersiz bazında kişisel rekorlar (en yüksek ağırlık)."""
    # Önce kullanıcının antrenman ID'lerini çek, sonra o ID'lere ait setleri sorgula
    workout_res = (
        supabase_admin.table("workouts")
        .select("id,date")
        .eq("user_id", user_id)
        .execute()
    )
    workout_map = {w["id"]: w["date"] for w in (workout_res.data or [])}
    if not workout_map:
        return []

    sets_res = (
        supabase_admin.table("workout_sets")
        .select("exercise_name,weight_kg,reps,workout_id")
        .in_("workout_id", list(workout_map.keys()))
        .execute()
    )
    prs: dict = {}
    for row in sets_res.data or []:
        ex = row["exercise_name"]
        if ex not in prs or (row["weight_kg"] or 0) > prs[ex]["weight_kg"]:
            prs[ex] = {
                "exercise":  ex,
                "weight_kg": row["weight_kg"] or 0,
                "reps":      row["reps"],
                "date":      workout_map.get(row["workout_id"]),
            }
    return sorted(prs.values(), key=lambda x: x["weight_kg"], reverse=True)[:10]

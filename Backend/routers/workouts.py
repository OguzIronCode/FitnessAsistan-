from fastapi import APIRouter, HTTPException, Query, Depends
from db.supabase import supabase_admin
from models.schemas import WorkoutCreate, SetCreate, WorkoutResponse, BodyMetricCreate
from utils.auth import get_current_user
from datetime import date

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


def assert_workout_owner(workout_id: str, user_id: str) -> None:
    res = (
        supabase_admin.table("workouts")
        .select("id")
        .eq("id", workout_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Antrenman bulunamadı")


# ─── Workouts ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[WorkoutResponse])
async def get_workouts(
    user_id: str = Depends(get_current_user),
    limit: int = Query(20, le=200),
):
    res = (
        supabase_admin.table("workouts")
        .select("*, programs(title)")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    result = []
    for row in res.data or []:
        prog = row.pop("programs", None) or {}
        row["program_title"] = prog.get("title") or row.get("notes") or "Serbest antrenman"
        result.append(WorkoutResponse(**row))
    return result


import re as _re
_UUID_RE = _re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', _re.I)


@router.post("", response_model=WorkoutResponse, status_code=201)
async def create_workout(data: WorkoutCreate, user_id: str = Depends(get_current_user)):
    # Yerel dataset ID'leri ("ds-0" vb.) Supabase'de yok; FK kısıtını aşmak için null yap
    program_id = data.program_id
    if program_id and not _UUID_RE.match(str(program_id)):
        program_id = None

    payload = {
        "user_id":     user_id,
        "date":        data.date.isoformat(),
        "program_id":  program_id,
        "duration_min": data.duration_min,
        "notes":       data.notes,
        "total_sets":  0,
    }
    res = supabase_admin.table("workouts").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Antrenman oluşturulamadı")
    row = res.data[0]
    row["program_title"] = data.notes or "Serbest antrenman"
    return WorkoutResponse(**row)


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(workout_id: str, user_id: str = Depends(get_current_user)):
    """Antrenmanı ve bağlı tüm setleri sil."""
    res = (
        supabase_admin.table("workouts")
        .delete()
        .eq("id", workout_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Antrenman bulunamadı")


@router.patch("/{workout_id}/finish")
async def finish_workout(
    workout_id: str,
    duration_min: int,
    user_id: str = Depends(get_current_user),
):
    """Antrenman bitiş süresi güncelle."""
    res = (
        supabase_admin.table("workouts")
        .update({"duration_min": duration_min})
        .eq("id", workout_id)
        .eq("user_id", user_id)
        .execute()
    )
    return {"status": "ok"}


# ─── Sets ─────────────────────────────────────────────────────────────────────

@router.post("/sets", status_code=201)
async def log_set(data: SetCreate, user_id: str = Depends(get_current_user)):
    """Bir set kaydet ve antrenman toplam_set sayısını artır."""
    assert_workout_owner(data.workout_id, user_id)
    payload = data.model_dump()
    payload["completed"] = True
    res = supabase_admin.table("workout_sets").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Set kaydedilemedi")

    # Toplam set sayısını güncelle
    supabase_admin.rpc("increment_total_sets", {"wid": data.workout_id}).execute()
    return res.data[0]


@router.get("/{workout_id}/sets")
async def get_sets(workout_id: str, _user_id: str = Depends(get_current_user)):
    assert_workout_owner(workout_id, _user_id)
    res = (
        supabase_admin.table("workout_sets")
        .select("*")
        .eq("workout_id", workout_id)
        .order("set_number")
        .execute()
    )
    return res.data or []


# ─── Body Metrics ─────────────────────────────────────────────────────────────

@router.post("/body-metrics", status_code=201)
async def add_body_metric(data: BodyMetricCreate, user_id: str = Depends(get_current_user)):
    payload = {"user_id": user_id, **data.model_dump()}
    payload["date"] = data.date.isoformat()
    res = supabase_admin.table("body_metrics").upsert(payload, on_conflict="user_id,date").execute()
    return res.data[0] if res.data else {}


@router.get("/body-metrics")
async def get_body_metrics(
    user_id: str = Depends(get_current_user),
    limit: int = Query(30),
):
    res = (
        supabase_admin.table("body_metrics")
        .select("*")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []

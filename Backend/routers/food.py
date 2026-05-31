from fastapi import APIRouter, HTTPException, Query, Depends
from db.supabase import supabase_admin
from models.schemas import FoodResponse
from utils.auth import get_current_user
from utils.openfoodfacts import search_foods, get_food_detail, get_food_by_barcode
from typing import Optional

router = APIRouter(prefix="/api/food", tags=["food"])


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val not in (None, "", "None") else None
    except (ValueError, TypeError):
        return None


# ── Yardımcı: Supabase satırını FoodResponse'a çevir ─────────────────────────
def _row_to_food(row: dict) -> FoodResponse:
    return FoodResponse(
        id=row["id"],
        name=row.get("name", ""),
        name_tr=row.get("name_tr") or row.get("name"),
        serving_size=row.get("serving_size", "100 g"),
        calories=_safe_float(row.get("calories")),
        protein=_safe_float(row.get("protein")),
        carbohydrate=_safe_float(row.get("carbohydrate")),
        fat=_safe_float(row.get("fat")),
        fiber=_safe_float(row.get("fiber")),
        sugars=_safe_float(row.get("sugars")),
        image_url=row.get("image_url"),
    )


# ── Open Food Facts sonucunu FoodResponse'a çevir ────────────────────────────
def _off_to_food(item: dict) -> FoodResponse:
    return FoodResponse(
        id=item.get("id", 0),
        name=item.get("name", ""),
        name_tr=item.get("name_tr") or item.get("name", ""),
        serving_size=item.get("serving_size", "100 g"),
        calories=_safe_float(item.get("calories")),
        protein=_safe_float(item.get("protein")),
        carbohydrate=_safe_float(item.get("carbohydrate")),
        fat=_safe_float(item.get("fat")),
        fiber=_safe_float(item.get("fiber")),
        sugars=_safe_float(item.get("sugars")),
        image_url=item.get("image_url"),
    )


@router.get("/search", response_model=list[FoodResponse])
async def search_food(
    q: str = Query(..., min_length=1, description="Aranacak besin adı"),
    limit: int = Query(20, le=50),
    _user_id: str = Depends(get_current_user),
):
    """
    Besin arama: önce Supabase cache, eksikse Open Food Facts API.
    Her sonuç resim URL'si içerir.
    """
    term = q.strip().lower()
    results: list[FoodResponse] = []
    seen_ids: set = set()

    # 1) Supabase cache'de ara (önceden kaydedilmiş besinler)
    try:
        tr_res = supabase_admin.table("foods").ilike("name_tr", f"%{term}%").limit(limit).execute()
        en_res = supabase_admin.table("foods").ilike("name",    f"%{term}%").limit(limit).execute()
        for row in (tr_res.data or []) + (en_res.data or []):
            if row["id"] not in seen_ids:
                seen_ids.add(row["id"])
                results.append(_row_to_food(row))
    except Exception:
        pass

    # 2) Open Food Facts'tan ara (kalan kapasite kadar)
    remaining = limit - len(results)
    if remaining > 0:
        try:
            fs_items = await search_foods(q, max_results=remaining)
            for item in fs_items:
                if item.get("id") and item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    results.append(_off_to_food(item))
        except Exception as e:
            # Open Food Facts erişilemezse sadece Supabase sonuçları döner
            if not results:
                raise HTTPException(status_code=503, detail=f"Besin servisi erişilemiyor: {e}")

    return results[:limit]


@router.get("/barcode/{barcode}")
async def get_by_barcode(
    barcode: str,
    _user_id: str = Depends(get_current_user),
):
    """Open Food Facts barkod API'si ile ürün sorgula."""
    # Önce Supabase'den dene
    if barcode.isdigit():
        try:
            fid = int(barcode)
            res = supabase_admin.table("foods").select("*").eq("id", fid).single().execute()
            if res.data:
                row = res.data
                return {
                    "barcode":      barcode,
                    "name":         row.get("name"),
                    "name_tr":      row.get("name_tr") or row.get("name"),
                    "serving_size": row.get("serving_size", "100 g"),
                    "calories":     _safe_float(row.get("calories")),
                    "protein":      _safe_float(row.get("protein")),
                    "carbohydrate": _safe_float(row.get("carbohydrate")),
                    "fat":          _safe_float(row.get("fat")),
                    "fiber":        _safe_float(row.get("fiber")),
                    "image_url":    row.get("image_url"),
                }
        except Exception:
            pass

    # Open Food Facts barkod sorgusunu dene
    item = await get_food_by_barcode(barcode)
    if item:
        return {
            "barcode":      barcode,
            "name":         item.get("name"),
            "name_tr":      item.get("name_tr") or item.get("name"),
            "serving_size": item.get("serving_size", "100 g"),
            "calories":     item.get("calories"),
            "protein":      item.get("protein"),
            "carbohydrate": item.get("carbohydrate"),
            "fat":          item.get("fat"),
            "fiber":        item.get("fiber"),
            "image_url":    item.get("image_url"),
        }

    raise HTTPException(status_code=404, detail="Ürün bulunamadı")


@router.get("/{food_id}", response_model=FoodResponse)
async def get_food(food_id: int, _user_id: str = Depends(get_current_user)):
    """Besin detayı: önce Supabase, yoksa Open Food Facts."""
    # Supabase'den dene
    try:
        res = (
            supabase_admin.table("foods")
            .select("id,name,name_tr,serving_size,calories,protein,carbohydrate,fat,fiber,sugars,image_url")
            .eq("id", food_id)
            .single()
            .execute()
        )
        if res.data:
            return _row_to_food(res.data)
    except Exception:
        pass

    # Open Food Facts'tan detay çek
    item = await get_food_detail(food_id)
    if item:
        return _off_to_food(item)

    raise HTTPException(status_code=404, detail="Besin bulunamadı")

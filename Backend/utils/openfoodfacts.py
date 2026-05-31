"""Open Food Facts API istemcisi (anahtarsiz, acik API).

Kullanim: Arama ve barkodla urun getirme. Turkce isim onceliklidir.
"""
from __future__ import annotations

from typing import Optional
import httpx

OFF_SEARCH_URLS = [
    "https://tr.openfoodfacts.org/cgi/search.pl",
    "https://world.openfoodfacts.org/cgi/search.pl",
]
OFF_PRODUCT_URLS = [
    "https://tr.openfoodfacts.org/api/v2/product/{barcode}.json",
    "https://world.openfoodfacts.org/api/v2/product/{barcode}.json",
]


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val not in (None, "", "None") else None
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int:
    try:
        return int(str(val))
    except (ValueError, TypeError):
        return 0


def _pick_name(product: dict) -> tuple[str, Optional[str]]:
    name_tr = product.get("product_name_tr") or product.get("product_name")
    name_en = product.get("product_name") or name_tr or ""
    return name_en, name_tr


def _parse_product(product: dict) -> dict:
    nutr = product.get("nutriments") or {}
    name, name_tr = _pick_name(product)

    calories = (
        _safe_float(nutr.get("energy-kcal_100g"))
        or _safe_float(nutr.get("energy-kcal"))
        or _safe_float(nutr.get("energy_100g"))
    )

    return {
        "id":           _safe_int(product.get("code")),
        "name":         name,
        "name_tr":      name_tr or name,
        "serving_size": product.get("serving_size") or "100 g",
        "calories":     calories,
        "protein":      _safe_float(nutr.get("proteins_100g")),
        "carbohydrate": _safe_float(nutr.get("carbohydrates_100g")),
        "fat":          _safe_float(nutr.get("fat_100g")),
        "fiber":        _safe_float(nutr.get("fiber_100g")),
        "sugars":       _safe_float(nutr.get("sugars_100g")),
        "image_url":    product.get("image_front_url") or product.get("image_url"),
    }


async def search_foods(query: str, max_results: int = 20, page: int = 1) -> list[dict]:
    """Besin arama (Open Food Facts)."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": max_results,
        "lc": "tr",
        "fields": ",".join([
            "code",
            "product_name",
            "product_name_tr",
            "serving_size",
            "nutriments",
            "image_front_url",
            "image_url",
        ]),
    }

    last_error: Exception | None = None
    data = None
    async with httpx.AsyncClient(timeout=15) as client:
        for url in OFF_SEARCH_URLS:
            try:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
                break
            except Exception as exc:
                last_error = exc
                data = None
                continue
    if data is None:
        raise last_error or RuntimeError("Open Food Facts arama istegi basarisiz")

    products = data.get("products") or []
    results: list[dict] = []
    for p in products:
        item = _parse_product(p)
        # Turkce isim olmayanlari elemek isterseniz bu satiri acin:
        # if not item.get("name_tr"): continue
        results.append(item)
    return results


async def get_food_detail(food_id: int) -> Optional[dict]:
    """Barkod ile urun detayi."""
    if not food_id:
        return None
    last_error: Exception | None = None
    data = None
    params = {"fields": "code,product_name,product_name_tr,serving_size,nutriments,image_front_url,image_url", "lc": "tr"}

    async with httpx.AsyncClient(timeout=15) as client:
        for tmpl in OFF_PRODUCT_URLS:
            try:
                url = tmpl.format(barcode=str(food_id))
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
                break
            except Exception as exc:
                last_error = exc
                data = None
                continue
    if data is None:
        raise last_error or RuntimeError("Open Food Facts urun istegi basarisiz")

    if data.get("status") != 1:
        return None
    product = data.get("product") or {}
    return _parse_product(product)


async def get_food_by_barcode(barcode: str) -> Optional[dict]:
    """Barkod ile urun bul."""
    if not barcode:
        return None
    try:
        food_id = int(barcode)
    except Exception:
        return None
    return await get_food_detail(food_id)

"""FatSecret Platform API — OAuth 2.0 Client Credentials istemcisi.

Token 24 saat geçerli; modül seviyesinde önbelleğe alınır.
"""
import re
import time
import asyncio
import httpx
from typing import Optional
from config import settings

_TOKEN: Optional[str] = None
_TOKEN_EXPIRES: float = 0.0

FS_TOKEN_URL = "https://oauth.fatsecret.com/connect/token"
FS_API_URL   = "https://platform.fatsecret.com/rest/server.api"


async def _get_token() -> str:
    """Geçerli OAuth token döndür; süresi dolduysa yenile."""
    global _TOKEN, _TOKEN_EXPIRES
    if _TOKEN and time.time() < _TOKEN_EXPIRES - 60:
        return _TOKEN

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            FS_TOKEN_URL,
            data={
                "grant_type":    "client_credentials",
                "scope":         "basic",
                "client_id":     settings.fatsecret_client_id,
                "client_secret": settings.fatsecret_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        body = r.json()

    _TOKEN         = body["access_token"]
    _TOKEN_EXPIRES = time.time() + body.get("expires_in", 86400)
    return _TOKEN


async def _fs_request(params: dict) -> dict:
    """FatSecret API'ye yetkili istek gönder."""
    token = await _get_token()
    params["format"] = "json"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            FS_API_URL,
            data=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()


# ── Yardımcı: açıklama metnini ayrıştır ──────────────────────────────────────
_NUM = r"([\d.]+)"

def _parse_desc(desc: str) -> dict:
    """
    'Per 100g - Calories: 165kcal | Fat: 3.57g | Carbs: 0.00g | Prot: 31.02g'
    biçimindeki açıklamadan besin değerlerini çıkar.
    """
    out: dict = {}

    cal = re.search(rf"Calories:\s*{_NUM}\s*kcal", desc, re.I)
    fat = re.search(rf"Fat:\s*{_NUM}\s*g",        desc, re.I)
    crb = re.search(rf"Carbs:\s*{_NUM}\s*g",      desc, re.I)
    prt = re.search(rf"Prot:\s*{_NUM}\s*g",       desc, re.I)

    if cal: out["calories"]      = float(cal.group(1))
    if fat: out["fat"]           = float(fat.group(1))
    if crb: out["carbohydrate"]  = float(crb.group(1))
    if prt: out["protein"]       = float(prt.group(1))

    # Porsiyon: "Per 1 piece (85g)" veya "Per 100g"
    srv = re.match(r"Per\s+(.+?)\s+-", desc)
    if srv:
        out["serving_size"] = srv.group(1).strip()

    # 100g bazına normalize et
    gram_match = re.search(r"\((\d+(?:\.\d+)?)\s*g\)", out.get("serving_size", ""))
    if gram_match:
        factor = 100 / float(gram_match.group(1))
        for key in ("calories", "fat", "carbohydrate", "protein"):
            if key in out:
                out[key] = round(out[key] * factor, 2)

    return out


# ── Görseli çek ───────────────────────────────────────────────────────────────
def _first_image(food_detail: dict) -> Optional[str]:
    imgs = food_detail.get("food_images") or {}
    img  = imgs.get("food_image")
    if not img:
        return None
    if isinstance(img, list):
        return img[0].get("image_url")
    if isinstance(img, dict):
        return img.get("image_url")
    return None


# ── Public API ────────────────────────────────────────────────────────────────

async def search_foods(query: str, max_results: int = 20, page: int = 0) -> list[dict]:
    """Besin arama — ad + temel makrolar + resim."""
    data = await _fs_request({
        "method":            "foods.search",
        "search_expression": query,
        "max_results":       max_results,
        "page_number":       page,
    })

    foods_wrap = data.get("foods", {})
    raw_list   = foods_wrap.get("food", [])
    if isinstance(raw_list, dict):   # tek sonuç → liste yap
        raw_list = [raw_list]

    # Her besin için görsel detayını paralel çek (max 10 paralel)
    sem = asyncio.Semaphore(10)

    async def enrich(item: dict) -> dict:
        nutrition = _parse_desc(item.get("food_description", ""))
        result = {
            "id":           int(item.get("food_id", 0)),
            "name":         item.get("food_name", ""),
            "name_tr":      item.get("food_name", ""),
            "serving_size": nutrition.pop("serving_size", "100 g"),
            "calories":     nutrition.get("calories"),
            "protein":      nutrition.get("protein"),
            "carbohydrate": nutrition.get("carbohydrate"),
            "fat":          nutrition.get("fat"),
            "fiber":        None,
            "sugars":       None,
            "image_url":    None,
        }
        # Görsel için food.get.v4 çağrısı
        async with sem:
            try:
                detail_data = await _fs_request({
                    "method":  "food.get.v4",
                    "food_id": item["food_id"],
                })
                food_obj = detail_data.get("food", {})
                result["image_url"] = _first_image(food_obj)
                # Daha hassas besin değerleri (v4'ten)
                servings = food_obj.get("servings", {})
                serving  = servings.get("serving")
                if isinstance(serving, list):
                    serving = next((s for s in serving
                                    if "100" in str(s.get("serving_description",""))), serving[0])
                if isinstance(serving, dict):
                    def _f(k): return float(serving[k]) if serving.get(k) else None
                    result.update({
                        "calories":     _f("calories"),
                        "protein":      _f("protein"),
                        "carbohydrate": _f("carbohydrate"),
                        "fat":          _f("fat"),
                        "fiber":        _f("fiber"),
                        "sugars":       _f("sugar"),
                    })
            except Exception:
                pass  # Görsel alınamazsa temel verilerle devam
        return result

    results = await asyncio.gather(*[enrich(item) for item in raw_list])
    return list(results)


async def get_food_detail(food_id: int) -> Optional[dict]:
    """Tek besin detayı — tüm makrolar + resim."""
    try:
        data = await _fs_request({"method": "food.get.v4", "food_id": str(food_id)})
        food_obj = data.get("food", {})
        if not food_obj:
            return None

        servings = food_obj.get("servings", {})
        serving  = servings.get("serving")
        if isinstance(serving, list):
            serving = next((s for s in serving
                            if "100" in str(s.get("serving_description",""))), serving[0])

        def _f(k): return float(serving[k]) if serving and serving.get(k) else None

        return {
            "id":           food_id,
            "name":         food_obj.get("food_name", ""),
            "name_tr":      food_obj.get("food_name", ""),
            "serving_size": serving.get("serving_description","100 g") if serving else "100 g",
            "calories":     _f("calories"),
            "protein":      _f("protein"),
            "carbohydrate": _f("carbohydrate"),
            "fat":          _f("fat"),
            "fiber":        _f("fiber"),
            "sugars":       _f("sugar"),
            "image_url":    _first_image(food_obj),
        }
    except Exception:
        return None


async def get_food_by_barcode(barcode: str) -> Optional[dict]:
    """Barkod ile besin bul."""
    try:
        data    = await _fs_request({"method": "food.find_id_for_barcode", "barcode": barcode})
        food_id = data.get("food_id", {}).get("value")
        if not food_id:
            return None
        return await get_food_detail(int(food_id))
    except Exception:
        return None

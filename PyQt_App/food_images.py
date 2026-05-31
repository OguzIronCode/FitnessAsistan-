import re
from pathlib import Path

FOOD_IMAGES_DIR = Path(__file__).parent.parent / "YiyecekGorselleri"


def _build_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    if not FOOD_IMAGES_DIR.exists():
        return index
    for img in FOOD_IMAGES_DIR.glob("*.jpg"):
        base = re.sub(r"_alt\d+$", "", img.stem).strip().lower()
        if base not in index:
            index[base] = img
        else:
            existing_alt = re.search(r"_alt(\d+)$", index[base].stem)
            new_alt = re.search(r"_alt(\d+)$", img.stem)
            if existing_alt and new_alt:
                if int(new_alt.group(1)) < int(existing_alt.group(1)):
                    index[base] = img
    return index


_FOOD_INDEX: dict[str, Path] = _build_index()


def find_food_image(food_name: str) -> str | None:
    if not food_name:
        return None
    key = food_name.strip().lower()

    if key in _FOOD_INDEX:
        return str(_FOOD_INDEX[key])

    for idx_key, path in _FOOD_INDEX.items():
        if key in idx_key or idx_key in key:
            return str(path)

    words = [w for w in key.split() if len(w) > 2]
    for idx_key, path in _FOOD_INDEX.items():
        if any(w in idx_key for w in words):
            return str(path)

    return None

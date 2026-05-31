"""
Basit test aracı: .env'deki FatSecret kimlik bilgileriyle token alır ve birkaç arama yapar.
Kullanım:
  cd Backend
  py -3 scripts\test_fatsecret.py

Not: Script gizli anahtarları yazdırmaz, sadece API yanıtlarının özetini gösterir.
"""
import os
import asyncio
from pathlib import Path
import json

# Load .env from Backend folder into environment
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        if '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

# ensure Backend package path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import fatsecret

async def run_tests():
    try:
        print('FatSecret token alınıyor...')
        token = await fatsecret._get_token()
        if token:
            print('Token alma başarılı (değer gösterilmiyor).')
        else:
            print('Token alınamadı (None).')

        queries = ['chicken', 'chicken breast', 'egg']
        for q in queries:
            print(f"Arama: '{q}' ...")
            try:
                res = await fatsecret.search_foods(q, max_results=5)
                print('  Sonuç sayısı:', len(res))
                for i, item in enumerate(res[:3]):
                    print('   -', item.get('id'), item.get('name'), f"cal={item.get('calories')}", 'has_image=' + str(bool(item.get('image_url'))))
            except Exception as e:
                print('  Aramada hata:', type(e).__name__, e)

    except Exception as e:
        print('Genel hata:', type(e).__name__, e)

if __name__ == '__main__':
    asyncio.run(run_tests())

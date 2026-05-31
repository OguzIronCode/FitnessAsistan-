from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.supabase import supabase

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Authorization: Bearer <supabase_access_token> header'ından
    kullanıcı kimliğini doğrula ve user_id döndür.
    """
    token = credentials.credentials
    try:
        res = supabase.auth.get_user(token)
        if res.user is None:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        return res.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Oturum doğrulanamadı")


def verify_token(token: str) -> str:
    """Token string'den user_id al (dependency dışı kullanım için)."""
    try:
        res = supabase.auth.get_user(token)
        if res.user is None:
            raise HTTPException(status_code=401, detail="Geçersiz token")
        return res.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Oturum doğrulanamadı")

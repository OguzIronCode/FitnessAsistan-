from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    secret_key: str = "offline-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    frontend_origin: str = "http://127.0.0.1:5500"
    fatsecret_client_id: str = ""
    fatsecret_client_secret: str = ""
    grok_api_key: str = ""
    grok_model: str = "llama-3.3-70b-versatile"
    grok_endpoint: str = "https://api.groq.com/openai/v1/chat/completions"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

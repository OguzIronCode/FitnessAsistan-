from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import auth, user, food, meals, workouts, analytics, ai, exercises

app = FastAPI(
    title="FitTrack AI API",
    description="Kişiselleştirilmiş fitness asistanı backend API'si",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(food.router)
app.include_router(meals.router)
app.include_router(workouts.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(exercises.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "app": "FitTrack AI API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}

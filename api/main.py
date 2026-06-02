from fastapi import FastAPI
from api.config import settings
from api.routers import auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Asynchronous Lightweight Infrastructure Monitoring Engine Backend Core",
    version="1.0.0"
)

# Core endpoints integration
app.include_router(auth.router)

@app.get("/health", tags=["System Check"])
async def system_health():
    """Simple operational verification status node."""
    return {"status": "operational"}

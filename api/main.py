import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis
from sqlalchemy.future import select

from api.config import settings
from api.database import AsyncSessionLocal, engine, Base
from api.models import User, Monitor, PingLog
from api.routers import auth, monitors
from workers.tasks import execute_http_ping

def _normalize_redis_url(redis_url: str) -> str:
    """Accept a full Redis URL or a raw Upstash URL/token and coerce it into a Redis scheme."""
    clean_url = redis_url.strip()
    if clean_url.startswith(("redis://", "rediss://", "unix://")):
        return clean_url
    return f"rediss://{clean_url}"


# Instantiate global thread-safe Upstash client connector
redis_client = aioredis.from_url(_normalize_redis_url(settings.REDIS_URL), decode_responses=True)


async def initialize_database_schema():
    """Create missing tables on startup so the app can boot cleanly on a fresh database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def continuous_monitoring_loop():
    """
    Continuous background worker daemon loop running inside the ASGI main thread.
    Periodically fetches active monitor targets, checks URLs, and caches states.
    """
    while True:
        async with AsyncSessionLocal() as db:
            try:
                query = select(Monitor).where(Monitor.is_active == True)
                result = await db.execute(query)
                active_monitors = result.scalars().all()

                eligible_monitors = [
                    monitor
                    for monitor in active_monitors
                    if monitor.monitor_type == "HTTP" and monitor.target_url
                ]

                tasks = [
                    execute_http_ping(monitor.id, monitor.target_url)
                    for monitor in eligible_monitors
                ]
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Store real-time status cache values inside Upstash Redis
                    for monitor, is_up in zip(eligible_monitors, results):
                        if not isinstance(is_up, Exception):
                            status_str = "UP" if is_up else "DOWN"
                            await redis_client.set(f"monitor:status:{monitor.id}", status_str)
            except Exception as loop_error:
                # Shield loop from dying on connection latency hiccups
                print(f"Background monitoring engine loop error: {str(loop_error)}")
        
        # Poll every 30 seconds for quick local testing and evaluation metrics
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown hooks cleanly."""
    await initialize_database_schema()
    # Startup: Launch the concurrent in-process background monitoring loop
    bg_task = asyncio.create_task(continuous_monitoring_loop())
    yield
    # Shutdown: Clean up resources and cancel the background worker task
    bg_task.cancel()
    await redis_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Asynchronous Lightweight Infrastructure Monitoring Engine Backend Core",
    version="1.0.0",
    lifespan=lifespan
)

# Incorporate active routers
app.include_router(auth.router)
app.include_router(monitors.router)

@app.get("/health", tags=["System Check"])
async def system_health():
    return {"status": "operational"}

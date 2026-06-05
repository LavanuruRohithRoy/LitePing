import time
import httpx
from api.database import AsyncSessionLocal
from api.models import PingLog

async def execute_http_ping(monitor_id: str, url: str) -> bool:
    """
    Executes a non-blocking asynchronous HTTP GET request against a target URL.
    Calculates operational latencies and logs failures safely inside the database session context.
    """
    start_time = time.perf_counter()
    status_code = None
    response_time_ms = None
    is_up = False
    error_message = None

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            status_code = response.status_code
            response_time_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Standard operational boundary: status codes 2xx and 3xx denote a healthy system
            if 200 <= status_code < 400:
                is_up = True
            else:
                error_message = f"Unhealthy network response code: {status_code}"
        except httpx.RequestError as exc:
            response_time_ms = int((time.perf_counter() - start_time) * 1000)
            error_message = f"Network connection failed: {str(exc)}"

    async with AsyncSessionLocal() as db:
        log_entry = PingLog(
            monitor_id=monitor_id,
            status_code=status_code,
            response_time_ms=response_time_ms,
            is_up=is_up,
            error_message=error_message
        )
        db.add(log_entry)
        await db.commit()
    return is_up

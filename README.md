# LitePing Engine

LitePing is an open-source, lightweight, self-hosted infrastructure monitoring system. It provides real-time HTTP availability checking and background performance metrics using a highly concurrent, single-process asynchronous engine.

## 🛠️ System Stack
- **Core API Engine:** Python 3.11 / FastAPI (Native Asynchronous ASGI with Lifespan Hooks)
- **Data Persistence:** PostgreSQL 15 & SQLAlchemy 2.0 (Async Driver Mappings)
- **Database Migrations Engine:** Alembic (Asynchronous Environment Pipeline)
- **Data Validation & Filtering:** Pydantic V2 & Email-Validator
- **Caching Layer & State Storage:** Serverless Redis via Upstash
- **Cryptographic Security:** Passlib (Bcrypt) & PyJWT (HMAC-SHA256)

---

## ⚙️ In-Process Concurrency & Monitoring Architecture

To remain cloud free-tier compliant, LitePing implements an integrated, non-blocking asynchronous architecture that eliminates the need for separate background worker containers.

```text
       [FastAPI ASGI Web Server Entrypoint]
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
[REST HTTP Controllers]       [Native Lifespan Context]
(Auth / Monitor CRUD)                  │
         │                             ▼
         │                 [asyncio Long-Running Loop]
         │                             │
         │                             ▼
         │                 [Active Targets DB Lookup]
         │                             │
         │                             ▼
         │                 [asyncio.gather() Batching]
         │                             │
         ▼                             ▼
[PostgreSQL Database] ◄──── [httpx Async HTTP Request]
         │                             │
         │                             ▼
         └──────────────────► [Upstash Redis Real-time Cache]
```

- **Lifespan Daemon Loop**: On application boot, an asynchronous event loop task is mounted inside the main process via `asyncio.create_task()`. It polls targets every 30 seconds without blocking the core HTTP worker paths.
- **Concurrent Task Batching**: Target requests are batched using `asyncio.gather()`. This executes multiple network checks simultaneously, scaling easily to handle hundreds of websites.
- **Real-Time Caching Structure**: Live availability metrics are written to Upstash Redis strings (`monitor:status:<id>`) for instant read access, while precise timestamp records are flushed to PostgreSQL for historical charting.

---

## 🚀 Local Development Setup & Operations

### 1. Boot Local Storage Infrastructure
Spin up your background PostgreSQL storage node:
```bash
docker compose up -d
```

### 2. Configure Database Migrations
Initialize the structural layouts inside your running PostgreSQL container using Alembic:
```powershell
alembic upgrade head
```

### 3. Run Application Live Reloader
Activate your virtual environment and start your local server:
```powershell
.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload
```

### 4. API Sandbox Matrix Check
Visit your local sandbox interface to interact with your code:
- **Swagger Documentation URL**: `http://127.0.0.1:8000/docs`
- **Target Generation Node**: `POST /monitors` (Protected route; requires JWT Bearer authorization)
- **Historical Analysis Node**: `GET /monitors/{id}/logs` (Fetches metrics records)

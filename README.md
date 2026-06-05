# LitePing Engine

LitePing is an open-source, lightweight, self-hosted developer-first infrastructure monitoring system. It provides real-time HTTP availability checking, network latency tracking, and passive cron backstop logging via a highly concurrent, single-process asynchronous engine.

## 🎯 The Core Problem & Product Efficacy
Existing enterprise infrastructure monitoring platforms (e.g., Datadog, Better Stack, Uptime Robot) enforce strict, highly monetization-driven limitations on their free tiers. They restrict developers to a handful of endpoints, enforce coarse evaluation frequencies (5+ minutes), and paywall custom notification hooks. Upgrading past these limits triggers significant monthly subscription overheads (\$20 to \$100+).

LitePing completely democratizes this layer by offering a 100% free, self-hosted engine. By combining the API routing and telemetry pooling into a single runtime thread using **FastAPI lifespans** and **`asyncio.gather()` batching**, the system maintains an ultra-low memory footprint of **under 120MB of RAM**. This makes it fully deployable on low-resource free cloud hosting tiers, allowing independent developers, open-source maintainers, and homelab hobbyists to retain complete ownership of their telemetry.

---

## 🏗️ Technical Architecture Blueprint

```text
         [FastAPI ASGI Web Server Process Base]
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
[REST HTTP Controllers]            [Native Lifespan Context]
(Auth / Monitor CRUD)                        │
         │                                   ▼
         │                      [asyncio Background Daemon]
         │                                   │
         │                                   ▼
         │                      [Active Targets Database Query]
         │                                   │
         │                                   ▼
         │                      [asyncio.gather() I/O Batching]
         │                                   │
         ▼                                   ▼
[PostgreSQL Database] ◄────────── [httpx Async Network Ping]
 (Long-Term Telemetry)                       │
         │                                   ▼
         └───────────────────────► [Upstash Serverless Redis Cache]
                                    (Real-Time Availability Flags)
```

### Core Architecture Components
*   **Unified Concurrency Core:** Eliminates separate, heavy background worker processes (like Celery) to sit within tight cloud RAM caps. All loops execute natively on the primary ASGI thread using non-blocking asynchronous calls.
*   **Asynchronous Processing:** Powered by Python's `asyncio` loop matrix. It handles up to 100 concurrent URLs every 30 seconds without blocking user-facing API request threads.
*   **Hybrid Storage Engine:** Splitting storage tasks according to performance needs. Real-time availability changes write directly to serverless **Upstash Redis** strings for instant client reading, while precise millisecond latency charts are flushed asynchronously to **PostgreSQL**.

---

## 🛠️ Complete Technical Stack
- **Web Runtime Core:** Python 3.11 / FastAPI (Native Asynchronous ASGI)
- **Data Persistence:** PostgreSQL 15 & SQLAlchemy 2.0 (Async Driver Mappings)
- **Database Migrations:** Alembic (Dynamic Environment Parameter Ingestion)
- **Data Sanitization:** Pydantic V2 & Email-Validator
- **Caching Layer:** Serverless Redis via Upstash
- **Cryptographic Security:** Passlib (Bcrypt) & PyJWT (HMAC-SHA256)

---

## 📖 Deep Engineering Documentation Manuals
For absolute systemic transparency regarding our design parameters, components, and trade-offs, review our dedicated technical whitepapers inside the `docs/` folder:
- 📄 [01. System Vision, Reality, & Strategic Engineering](./docs/system_vision.md) — Problem metrics and explicit cloud compromises.
- 📄 [02. Component Matrix & Database Schema](./docs/component_matrix.md) — File-by-file blueprint mapping and relational ER diagrams.
- 📄 [03. Runtime Operations & Concurrency](./docs/runtime_pipeline.md) — Asynchronous loop execution timelines and task batching.
- 📄 [04. Controller Specs & Response Schemas](./docs/controller_specs.md) — Endpoint pathways validation matrix guidelines.
- 📄 [05. Strategic Vision & Developer Economics](./docs/project_vision.md) — Phase-by-phase scaling roadmap parameters.

---

## 🚀 Realistic Local Development Setup
This repo is intentionally lightweight. A first local setup only needs Python, Docker, and the environment variables below.

### 1. Create the local environment file
Create a `.env` file in the repository root:
```env
PROJECT_NAME="LitePing Engine"
SECRET_KEY="replace-with-a-long-random-string"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/liteping"
REDIS_URL="redis://default:your_upstash_password@your_endpoint.upstash.io:6379/0"
```

Notes:
- `DATABASE_URL` points to the local Postgres container from `docker-compose.yml`.
- `REDIS_URL` is only needed for live status caching; for deployment it can point to Upstash.
- `SECRET_KEY` should be unique per machine or environment.

### 2. Start the database
Bring up the local PostgreSQL container:
```powershell
docker compose up -d
```

Optional check:
```powershell
docker ps
```

### 3. Activate the virtual environment
Use the workspace venv before running migrations or tests:
```powershell
.venv\Scripts\Activate.ps1
```

### 4. Run the database migrations
Apply the current schema to the local database:
```powershell
alembic upgrade head
```

### 5. Start the API server
Launch FastAPI with auto-reload:
```powershell
uvicorn api.main:app --reload
```

Useful local URLs:
- `http://127.0.0.1:8000/docs` — interactive OpenAPI UI
- `http://127.0.0.1:8000/health` — lightweight health check

---

## 🧪 Test Specification & Validation

LitePing uses a small, focused `unittest` suite to keep validation fast and dependency-light.

### What the tests cover
- **Auth flow:** registration duplicate handling and token login.
- **Monitor flow:** create, list, delete, and log retrieval for owned monitors.
- **Runtime worker:** successful and failed HTTP checks write `PingLog` rows.
- **Background loop:** only HTTP monitors are checked, and status updates map to the correct monitor IDs.
- **Health check:** the system health endpoint returns the expected operational payload.

### How to run locally
```powershell
python -m unittest discover -s tests -v
```

### What a passing run means
- The main request flow is wired correctly.
- The worker can ping targets and persist logs.
- The in-process scheduler behavior matches the intended monitor lifecycle.

---

## ☁️ Production Cloud Deployment Blueprint (Render + Upstash)

LitePing features fully integrated **Infrastructure-as-Code Blueprint Manifests** allowing one-click cluster generation on 100% free hosting tiers:

1.  Provision a free serverless Redis database instance on [Upstash Console](https://upstash.com). Copy the secure `redis://` connection URL token.
2.  Push your customized repository branch directly up to your public GitHub profile.
3.  Log into your [Render Cloud Console](https://render.com). Click **New +** and select the **Blueprint** option.
4.  Link your target GitHub repository. Render will automatically parse your `render.yaml` specification file and configure your web application and database containers.
5.  Paste your copied Upstash connection string into the `REDIS_URL` environment parameter variable block on the dashboard panel UI and hit deploy. Render will automatically handle your SSL certificates and boot the engine live.

`render.yaml` is a deployment manifest, not a local-development requirement. It exists so the same project can be booted from Render with consistent environment settings and a managed Postgres database when you are ready to publish.

---

## 🎯 Strategic Scaling Roadmap
Because the code was built completely decoupled from day one, transitioning this project from a homelab utility into an enterprise system requires zero core rewrites:
- **Phase 1: Horizontal Expansion:** Multiple identical app containers can be deployed behind a load balancer (Nginx / AWS ALB) to split traffic, reading and writing to the same central database.
- **Phase 2: Independent Worker Offloading:** If tracking capacity grows to thousands of sites, the polling loops can be moved from the lifespan thread pool directly into dedicated background worker clusters without modifying schemas.
- **Phase 3: Time-Series Storage Integration:** As append-only logging tables grow past tens of millions of rows, standard PostgreSQL can convert into **TimescaleDB** with a single click, keeping chronological performance metrics lookups instant.

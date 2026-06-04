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
- 📄 [01. System Vision, Reality, & Strategic Engineering](./docs/01_system_vision.md) — Problem metrics and explicit cloud compromises.
- 📄 [02. Component Matrix & Database Schema](./docs/02_component_matrix.md) — File-by-file blueprint mapping and relational ER diagrams.
- 📄 [03. Runtime Operations & Concurrency](./docs/03_runtime_pipelines.md) — Asynchronous loop execution timelines and task batching.
- 📄 [04. Controller Specs & Response Schemas](./docs/04_controller_specs.md) — Endpoint pathways validation matrix guidelines.
- 📄 [05. Strategic Vision & Developer Economics](./docs/05_project_vision.md) — Phase-by-phase scaling roadmap parameters.
- 📂 [Technical Documentation Index Manual](./docs/README.md) — The central index matrix guide.

---

## 🚀 Realistic Local Development Setup

### 1. Configure the Local Environment Variables
Create a file named `.env` in the root folder of your project workspace to feed variables safely into Pydantic Settings:
```env
PROJECT_NAME="LitePing Engine"
SECRET_KEY="your_secure_development_random_cryptographic_hash_string"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Local Container Storage Variables
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/liteping"

# Upstash Connection Variables (Paste your real Upstash token string here)
REDIS_URL="redis://default:your_upstash_password@your_endpoint.upstash.io:6379/0"
```

### 2. Boot Your Background PostgreSQL Storage Node
Spin up the isolated database container using Docker Compose:
```bash
docker compose up -d
```
Verify that the database node is online and listening on its network interface:
```bash
docker ps
```

### 3. Initialize and Execute Your Local Database Migrations
Activate your local virtual environment layout, and run Alembic to apply structural table configurations natively inside your running database container:
```powershell
# Activate local isolated sandbox environment
.venv\Scripts\Activate.ps1

# Upgrade storage tables directly to latest version history
alembic upgrade head
```

### 4. Launch the ASGI Application Web Server
Boot up your FastAPI application using Uvicorn with auto-reload flags active:
```powershell
uvicorn api.main:app --reload
```
*   **Interactive OpenAPI Sandbox UI:** `http://127.0.0`
*   **System Health Probe Node:** `GET http://127.0.0`

---

## ☁️ Production Cloud Deployment Blueprint (Render + Upstash)

LitePing features fully integrated **Infrastructure-as-Code Blueprint Manifests** allowing one-click cluster generation on 100% free hosting tiers:

1.  Provision a free serverless Redis database instance on [Upstash Console](https://upstash.com). Copy the secure `redis://` connection URL token.
2.  Push your customized repository branch directly up to your public GitHub profile.
3.  Log into your [Render Cloud Console](https://render.com). Click **New +** and select the **Blueprint** option.
4.  Link your target GitHub repository. Render will automatically parse your `render.yaml` specification file and configure your web application and database containers.
5.  Paste your copied Upstash connection string into the `REDIS_URL` environment parameter variable block on the dashboard panel UI and hit deploy. Render will automatically handle your SSL certificates and boot the engine live.

---

## 🎯 Strategic Scaling Roadmap
Because the code was built completely decoupled from day one, transitioning this project from a homelab utility into an enterprise system requires zero core rewrites:
- **Phase 1: Horizontal Expansion:** Multiple identical app containers can be deployed behind a load balancer (Nginx / AWS ALB) to split traffic, reading and writing to the same central database.
- **Phase 2: Independent Worker Offloading:** If tracking capacity grows to thousands of sites, the polling loops can be moved from the lifespan thread pool directly into dedicated background worker clusters without modifying schemas.
- **Phase 3: Time-Series Storage Integration:** As append-only logging tables grow past tens of millions of rows, standard PostgreSQL can convert into **TimescaleDB** with a single click, keeping chronological performance metrics lookups instant.

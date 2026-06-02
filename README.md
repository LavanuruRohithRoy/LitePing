# LitePing Engine

LitePing is an open-source, lightweight, self-hosted infrastructure monitoring system. It provides real-time HTTP availability checking and background cron backstop metrics using a highly concurrent, single-process asynchronous engine.

## 🛠️ System Stack
- **Core Engine:** Python 3.11 / FastAPI (Asynchronous)
- **Data Persistence:** PostgreSQL 15 & SQLAlchemy 2.0 (Async Drivers)
- **Caching Layer:** Serverless Redis via Upstash

## 🚀 Local Development Infrastructure Setup

### 1. Boot Environment Database Container
Spin up the isolated local PostgreSQL storage layer:
```bash
docker compose up -d
```

### 2. Verify Storage Infrastructure Status
Ensure the database container node is successfully online and listening on its default internal network interface:
```bash
docker ps
```

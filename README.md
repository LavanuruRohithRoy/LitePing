# LitePing Engine

LitePing is an open-source, lightweight, self-hosted infrastructure monitoring system. It provides real-time HTTP availability checking and background cron backstop metrics using a highly concurrent, single-process asynchronous engine.

## 🛠️ Complete System Stack
- **Core API Engine:** Python 3.11 / FastAPI (Native Asynchronous ASGI)
- **Data Persistence:** PostgreSQL 15 & SQLAlchemy 2.0 (Async Drivers)
- **Data Validation & Filtering:** Pydantic V2 & Email-Validator
- **Cryptographic Security:** Passlib (Bcrypt) & PyJWT (HMAC-SHA256)

---

## 🔒 Security & Authentication Architecture

LitePing implements strict stateless authentication via OAuth2 using JSON Web Tokens (JWT). The system completely isolates raw internal database entries from network output operations.

### 1. Data Schema Isolation & Pipeline Flow
Incoming payloads undergo data sanitation checks via Pydantic before reaching the controller level.

```text
[Client Request Payload] 
       │
       ▼
[Pydantic Input Schema] (Enforces email-validator rules & length)
       │
       ▼
[Bcrypt Hashing & Verification] (Executes 12-round salt hashing)
       │
       ▼
[SQLAlchemy Async Engine] (Asynchronously flushes records to Postgres)
       │
       ▼
[Pydantic Output Filter] (Strips 'hashed_password' from memory fields)
       │
       ▼
[Client Network Response]
```

- **Input Ingestion (`api/schemas.py -> UserRegister`)**: Validates that incoming payloads provide syntactically accurate email addresses via strict regex lookups and ensures passwords pass minimum safety lengths (>= 6 characters).
- **Output Masking (`api/schemas.py -> UserResponse`)**: Explicitly controls network serialization. It selectively permits fields like `id`, `email`, and `created_at` to cross the wire while completely stripping the `hashed_password` from the JSON payload.

### 2. Cryptographic Security Standards
- **Password Safety**: Raw passwords are never stored. The engine passes credentials through a blowfish-based cipher context (`passlib[bcrypt]`) utilizing specialized, randomized 12-round workload salt cycles.
- **Stateless Verification Tokens**: Authentication issues a highly compressed, cryptographically signed bearer token via `HMAC-SHA256` containing an explicit payload signature expiration lifespan (`exp`) and the unique resource tracker identification string (`sub`).

---

## 🚀 Local Development Setup & Operations

### 1. Boot Local Storage Infrastructure
Spin up the isolated local PostgreSQL container engine in your background runtime environment:
```bash
docker compose up -d
```

### 2. Verify Storage Infrastructure Status
Ensure the database container node is successfully online and listening on its default internal network interface:
```bash
docker ps
```

### 3. Native Virtual Environment Execution
Activate your isolated Python sandbox package registry, mount dependencies, and initialize the ASGI loop server:
```powershell
# Create environment
python -m venv .venv

# PowerShell Execution Policy Bypass
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activation
.venv\Scripts\Activate.ps1

# Dependency Ingestion
pip install -r requirements.txt

# Run Application Live Reloader
uvicorn api.main:app --reload
```

### 4. API Sandbox Interaction Matrix
Once the local Uvicorn daemon binds to your network interfaces, visit the interactive OpenAPI sandbox interface to test endpoints:
- **Swagger Documentation URL**: `http://127.0.0`
- **Functional Check Node**: `GET /health` (Verifies loop processing health)
- **Account Generation Node**: `POST /auth/register` (Parses and writes clean records)
- **Token Verification Node**: `POST /auth/login` (Issues encrypted Bearer JWT components)

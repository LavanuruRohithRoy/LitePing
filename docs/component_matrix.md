# Section 2: Complete Component Matrix & Relational Schema Mapping

## 1. Deep File-by-File Component Mapping

```text
liteping/
├── api/
│   ├── routers/
│   │   ├── auth.py         -> Logic managing user creation, password hashing, and secure JWT generation.
│   │   └── monitors.py     -> Controller handling CRUD operations for targets and log lookups.
│   ├── main.py             -> Application entrypoint; handles CORS and spins up the background loop task.
│   ├── config.py           -> Strict environment configuration parser using Pydantic Settings. No hardcoding.
│   ├── database.py         -> Instantiates async SQLAlchemy connection pools and handles session management.
│   ├── models.py           -> Relational database schemas mapping out tables, data types, and indexes.
│   └── schemas.py          -> Pydantic models for incoming payload validation and outbound data serialization.
├── workers/
│   └── tasks.py            -> High-performance utility functions executing non-blocking HTTP requests.
├── alembic/                -> Database migration history tracks, environments, and version control scripts.
├── .github/
│   └── SECURITY.md         -> Governance documentation for reporting vulnerabilities privately.
├── .env                    # Active connection secrets storage (Excluded from git tracking).
├── .gitignore              # Shields the repository from junk files, caches, and configuration secrets.
├── alembic.ini             # Configuration parameters mapping Alembic schema migrations.
├── docker-compose.yml     # Local orchestration file mapping local Postgres development containers.
├── LICENSE                 # Legal permissive framework text (MIT License).
├── requirements.txt        # Frozen package dependencies list.
└── README.md               # User-facing open-source technical overview document.
```

---

## 2. Complete Database Relational Schema Layout

The database architecture is designed to enforce strict data integrity while optimizing query performance using composite indexes.

```text
┌────────────────────────────────────────────────────────┐
│                        users                           │
├────────────────────────────────────────────────────────┤
│ id              UUID         PRIMARY KEY (gen_uuid())  │
│ email           VARCHAR(255) UNIQUEINDEX, NOT NULL     │
│ hashed_password VARCHAR(255) NOT NULL                  │
│ created_at      TIMESTAMPTZ  DEFAULT NOW()             │
└────────────────────────────────────────────────────────┘
                           │
                           │ 1-to-Many Relation
                           ▼ (ondelete="CASCADE")
┌────────────────────────────────────────────────────────┐
│                       monitors                         │
├────────────────────────────────────────────────────────┤
│ id                     UUID         PRIMARY KEY        │
│ user_id                UUID         FOREIGN KEY        │
│ name                   VARCHAR(100) NOT NULL           │
│ monitor_type           VARCHAR(20)  DEFAULT "HTTP"     │
│ target_url             VARCHAR(512) NULL               │
│ check_interval_seconds INTEGER      DEFAULT 60         │
│ is_active              BOOLEAN      DEFAULT TRUE       │
│ created_at             TIMESTAMPTZ  DEFAULT NOW()      │
└────────────────────────────────────────────────────────┘
                           │
                           │ 1-to-Many Relation
                           ▼ (ondelete="CASCADE")
┌────────────────────────────────────────────────────────┐
│                      ping_logs                         │
├────────────────────────────────────────────────────────┤
│ id               BIGINT       PRIMARY KEY AUTOINCREMENT│
│ monitor_id       UUID         FOREIGN KEY              │
│ status_code      INTEGER      NULL                     │
│ response_time_ms INTEGER      NULL                     │
│ is_up            BOOLEAN      NOT NULL                 │
│ error_message    TEXT         NULL                     │
│ checked_at       TIMESTAMPTZ  DEFAULT NOW()            │
├────────────────────────────────────────────────────────┤
│ INDEX: idx_logs_monitor_time (monitor_id, checked_atDESC)│
└────────────────────────────────────────────────────────┘
```

### Component Integrity Details
- **`User` Table Boundary:** Acts as the primary anchor. The `email` column uses a strict string format length and is indexed to ensure fast account lookup times during authentication phases.
- **`Monitor` Table Boundary:** Stores tracking configurations. It links to the `users` table via an explicit `ondelete="CASCADE"` foreign key constraint. If a user deletes their account, the database automatically cleans up all associated monitors at the storage engine level.
- **`PingLog` Table Boundary:** A high-volume table designed for append-only telemetry logging. It connects to the `monitors` table via a cascading foreign key. Because fetching log charts requires querying the database chronologically, we implement a composite index (`monitor_id`, `checked_at DESC`). This allows the engine to instantly retrieve historical trends without performing slow, full-table scans.

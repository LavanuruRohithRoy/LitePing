# Section 3: Runtime Operations & In-Process Concurrency Engineering

## 1. App Lifecycles & Lifespan Injection Strategy
LitePing combines all application workflows into a single process runtime. It uses FastAPI's `lifespan` context manager to initialize background monitoring loops alongside standard user-facing HTTP endpoints.

```text
[Uvicorn Server Process Boots Up]
               │
               ▼
[api/main.py -> lifespan() Hook Fires]
               │
               ├──────────────────────────────────────────┐
               ▼                                          ▼
   [Mount HTTP Thread Pool]                  [asyncio.create_task()]
   (Listens for REST API Calls)               (Spawns Non-Blocking Background Daemon)
               │                                          │
               ▼                                          ▼
   [Ready for Client Ingestion]               [continuous_monitoring_loop()]
                                                          │
                                                          ▼
                                              [Enter Infinite execution state]
```

When the application finishes booting, the lifespan manager executes `asyncio.create_task(continuous_monitoring_loop())`. This mounts our background polling function onto the active ASGI event loop as a non-blocking background task. When the server shuts down, the loop catches the cancel signal, safely cancels the task, and closes all open database connection pools and Redis sockets cleanly.

---

## 2. Asynchronous Polling & Concurrent Task Batching Pipeline
The background loop executes on a continuous 30-second interval, checking all active monitor targets simultaneously without blocking the parent thread.

```text
[continuous_monitoring_loop iteration begins]
                      │
                      ▼
        [Open AsyncSessionLocal DB Session]
                      │
                      ▼
     [Fetch All Monitors Where is_active == True]
                      │
                      ▼
   [Loop Through Targets & Build Coroutine Array]
   tasks.append(execute_http_ping(monitor_id, url, db))
                      │
                      ▼
        [asyncio.gather(*tasks) Execution]
  (All external HTTP network requests fire at once)
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
 [workers/tasks.py]        [workers/tasks.py]
  (httpx Target A)          (httpx Target B)
         │                         │
         └────────────┬────────────┘
                      ▼
       [Compile Matrix Collection Arrays]
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
[Flush Log Row to Postgres] [Cache State String to Upstash]
         │                         │
         └────────────┬────────────┘
                      ▼
      [asyncio.sleep(30) Until Next Iteration]
```

### Execution Step Details
1. **Target Ingestion:** Every 30 seconds, the background task opens an `AsyncSession` database context and queries the database for active monitors.
2. **Task Generation:** The loop iterates over the results, generating non-blocking network tasks (`execute_http_ping`) and adding them to an execution array.
3. **Concurrent Batching:** The system triggers `asyncio.gather(*tasks)`. This fires all network requests across the wire at the same time, maximizing I/O performance.
4. **Data Persistence:** The engine writes detailed latency records to PostgreSQL and updates live statuses in Upstash Redis for instant retrieval. The database session is then closed cleanly, and the task sleeps until the next interval.

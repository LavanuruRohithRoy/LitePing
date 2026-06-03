# Section 4: Controller Routing Matrix & Security Verification Specifications

## 1. Authentication Controller (`api/routers/auth.py`)
Provides public entrypoints for user onboarding and token issuance.

### POST /auth/register
Registers a new developer account.
- **Input Model Requirements (`UserRegister`):** Parses JSON payloads, validating email formatting via `email-validator` and ensuring passwords pass minimum safety rules (>= 6 characters).
- **Execution Processing:** Performs an optimized database lookup to prevent duplicate emails. If the email is unique, it passes the plain-text password to `passlib[bcrypt]`, executing a 12-round workload salt before saving the user record.
- **Output Model Response (`UserResponse`):** Status `201 Created`. Filters out the password hash, returning only safe fields:
  ```json
  {
    "id": "c7b2a9d4-e6f1-432a-b9c8-d7e6f5a4b3c2",
    "email": "developer@domain.local",
    "created_at": "2026-06-03T15:15:30Z"
  }
  ```

### POST /auth/login
Validates user credentials and issues a secure access token. Complies with the standard OAuth2 specification by accepting URL-encoded Form-Data inputs.
- **Input Parameters:** Form fields `username` (email) and `password`.
- **Execution Processing:** Retrieves the user by email, verifies the password hash, and generates an encrypted JSON Web Token (JWT) signed with your `SECRET_KEY` via `HMAC-SHA256`.
- **Output Model Response (`Token`):** Status `200 OK`. Returns a bearer token used to authenticate protected endpoints:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

---

## 2. Infrastructure Management Controller (`api/routers/monitors.py`)
Handles target configurations and telemetry logs. All endpoints below are protected and require a valid `Authorization: Bearer <token>` header.

### POST /monitors
Configures a new application target for active tracking.
- **Input Model Requirements (`MonitorCreate`):** Validate input parameters, enforcing interval minimums (>= 10 seconds) and valid URL shapes.
- **Security Check:** Evaluates the client token. If valid, binds the new monitor directly to the authenticated user's ID.

### GET /monitors
Returns all active monitoring targets owned by the authenticated developer profile.
- **Output Model Response:** Status `200 OK`. Returns an array of configurations (`MonitorResponse`).

### DELETE /monitors/{monitor_id}
Removes a tracking target from the system and deletes its entire log history.
- **Execution Processing:** Verifies the authenticated user owns the target monitor before running the delete operation, triggering database-level cascading purges. Returns Status `204 No Content`.

### GET /monitors/{monitor_id}/logs
Fetches chronological performance data for an active monitor target to build availability charts.
- **Execution Processing:** Queries the database using our composite index, retrieving the 100 most recent ping logs (`PingLogResponse`) sorted by timestamp:
  ```json
  [
    {
      "id": 98451,
      "status_code": 200,
      "response_time_ms": 14,
      "is_up": true,
      "error_message": null,
      "checked_at": "2026-06-03T15:16:00Z"
    }
  ]
  ```

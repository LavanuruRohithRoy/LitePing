import uuid
import os
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/liteping")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from fastapi import HTTPException

from api.models import Monitor, PingLog, User
from api.routers.auth import login, register
from api.routers.monitors import create_monitor, delete_monitor, get_monitor_metrics, list_monitors
from api.schemas import MonitorCreate, UserRegister
from api.main import system_health


class FakeScalarResult:
    def __init__(self, items):
        self._items = list(items)

    def first(self):
        return self._items[0] if self._items else None

    def all(self):
        return list(self._items)


class FakeResult:
    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return FakeScalarResult(self._items)


class FakeSession:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.added = []
        self.deleted = []
        self.flushed = 0

    async def execute(self, query):
        if not self.results:
            raise AssertionError("Unexpected database query")
        return FakeResult(self.results.pop(0))

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed += 1

    async def delete(self, obj):
        self.deleted.append(obj)


class TestApiRoutes(IsolatedAsyncioTestCase):
    async def test_health_endpoint(self):
        self.assertEqual(await system_health(), {"status": "operational"})

    async def test_register_rejects_duplicate_email(self):
        user = User(id=uuid.UUID("00000000-0000-0000-0000-000000000000"), email="dev@example.com", hashed_password="x")
        db = FakeSession(results=[[user]])

        with self.assertRaises(HTTPException) as ctx:
            await register(UserRegister(email="dev@example.com", password="secret123"), db=db)

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_register_creates_user(self):
        db = FakeSession(results=[[]])

        with patch("api.routers.auth.hash_password", return_value="hashed-password"):
            new_user = await register(UserRegister(email="new@example.com", password="secret123"), db=db)

        self.assertEqual(new_user.email, "new@example.com")
        self.assertEqual(new_user.hashed_password, "hashed-password")
        self.assertEqual(db.flushed, 1)
        self.assertEqual(len(db.added), 1)

    async def test_login_returns_token(self):
        user = User(id=uuid.UUID("11111111-1111-1111-1111-111111111111"), email="dev@example.com", hashed_password="hashed")
        db = FakeSession(results=[[user]])
        form = SimpleNamespace(username="dev@example.com", password="secret123")

        with patch("api.routers.auth.verify_password", return_value=True), patch(
            "api.routers.auth.create_access_token", return_value="token-value"
        ):
            token = await login(form_data=form, db=db)

        self.assertEqual(token["access_token"], "token-value")
        self.assertEqual(token["token_type"], "bearer")

    async def test_create_monitor_requires_http_target(self):
        user = User(id=uuid.UUID("22222222-2222-2222-2222-222222222222"), email="dev@example.com", hashed_password="hashed")
        db = FakeSession()

        with self.assertRaises(HTTPException) as ctx:
            await create_monitor(
                MonitorCreate(name="api", monitor_type="HTTP", target_url=None, check_interval_seconds=60),
                db=db,
                current_user=user,
            )

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_create_monitor_persists_target(self):
        user = User(id=uuid.UUID("22222222-2222-2222-2222-222222222222"), email="dev@example.com", hashed_password="hashed")
        db = FakeSession()

        monitor = await create_monitor(
            MonitorCreate(name="api", monitor_type="HTTP", target_url="https://example.com", check_interval_seconds=30),
            db=db,
            current_user=user,
        )

        self.assertEqual(monitor.user_id, user.id)
        self.assertEqual(monitor.target_url, "https://example.com")
        self.assertEqual(db.flushed, 1)
        self.assertEqual(len(db.added), 1)

    async def test_list_monitors_returns_owned_items(self):
        user = User(id=uuid.UUID("33333333-3333-3333-3333-333333333333"), email="dev@example.com", hashed_password="hashed")
        monitor = Monitor(
            id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
            user_id=user.id,
            name="api",
            monitor_type="HTTP",
            target_url="https://example.com",
            check_interval_seconds=30,
            is_active=True,
        )
        db = FakeSession(results=[[monitor]])

        monitors = await list_monitors(db=db, current_user=user)

        self.assertEqual(len(monitors), 1)
        self.assertEqual(monitors[0].name, "api")

    async def test_delete_monitor_removes_owned_item(self):
        user = User(id=uuid.UUID("55555555-5555-5555-5555-555555555555"), email="dev@example.com", hashed_password="hashed")
        monitor = Monitor(
            id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
            user_id=user.id,
            name="api",
            monitor_type="HTTP",
            target_url="https://example.com",
            check_interval_seconds=30,
            is_active=True,
        )
        db = FakeSession(results=[[monitor]])

        await delete_monitor(monitor_id=monitor.id, db=db, current_user=user)

        self.assertEqual(db.deleted, [monitor])

    async def test_get_monitor_metrics_returns_recent_logs(self):
        user = User(id=uuid.UUID("77777777-7777-7777-7777-777777777777"), email="dev@example.com", hashed_password="hashed")
        monitor = Monitor(
            id=uuid.UUID("88888888-8888-8888-8888-888888888888"),
            user_id=user.id,
            name="api",
            monitor_type="HTTP",
            target_url="https://example.com",
            check_interval_seconds=30,
            is_active=True,
        )
        log = PingLog(
            id=1,
            monitor_id=monitor.id,
            status_code=200,
            response_time_ms=15,
            is_up=True,
            error_message=None,
        )
        db = FakeSession(results=[[monitor], [log]])

        logs = await get_monitor_metrics(monitor_id=monitor.id, db=db, current_user=user)

        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].is_up)

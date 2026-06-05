import uuid
import asyncio
import os
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/liteping")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import httpx

from api.models import Monitor
from workers.tasks import execute_http_ping
from api.main import continuous_monitoring_loop


class FakeResult:
    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return self

    def all(self):
        return list(self._items)


class FakeSession:
    def __init__(self, monitors):
        self.monitors = list(monitors)
        self.added = []
        self.committed = 0

    async def execute(self, query):
        return FakeResult(self.monitors)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed += 1


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeHTTPResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeHTTPClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        if self.error is not None:
            raise self.error
        return self.response


class TestRuntime(IsolatedAsyncioTestCase):
    async def test_execute_http_ping_writes_success_log(self):
        session = FakeSession(monitors=[])
        request = httpx.Request("GET", "https://example.com")
        error = httpx.RequestError("boom", request=request)

        with patch("workers.tasks.AsyncSessionLocal", return_value=FakeSessionContext(session)), patch(
            "workers.tasks.httpx.AsyncClient", return_value=FakeHTTPClient(response=FakeHTTPResponse(200))
        ):
            is_up = await execute_http_ping("monitor-1", "https://example.com")

        self.assertTrue(is_up)
        self.assertEqual(session.committed, 1)
        self.assertEqual(len(session.added), 1)
        self.assertEqual(session.added[0].monitor_id, "monitor-1")
        self.assertEqual(session.added[0].status_code, 200)

    async def test_execute_http_ping_writes_failure_log(self):
        session = FakeSession(monitors=[])
        request = httpx.Request("GET", "https://example.com")
        error = httpx.RequestError("boom", request=request)

        with patch("workers.tasks.AsyncSessionLocal", return_value=FakeSessionContext(session)), patch(
            "workers.tasks.httpx.AsyncClient", return_value=FakeHTTPClient(error=error)
        ):
            is_up = await execute_http_ping("monitor-1", "https://example.com")

        self.assertFalse(is_up)
        self.assertEqual(session.committed, 1)
        self.assertEqual(session.added[0].error_message.startswith("Network connection failed:"), True)

    async def test_continuous_monitoring_loop_maps_statuses_to_correct_monitors(self):
        http_one = Monitor(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            user_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="http-one",
            monitor_type="HTTP",
            target_url="https://one.example.com",
            check_interval_seconds=30,
            is_active=True,
        )
        cron_monitor = Monitor(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            user_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="cron-one",
            monitor_type="CRON",
            target_url=None,
            check_interval_seconds=30,
            is_active=True,
        )
        http_two = Monitor(
            id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
            user_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="http-two",
            monitor_type="HTTP",
            target_url="https://two.example.com",
            check_interval_seconds=30,
            is_active=True,
        )
        session = FakeSession(monitors=[http_one, cron_monitor, http_two])
        redis_set = AsyncMock()

        async def stop_after_one_sleep(seconds):
            raise asyncio.CancelledError()

        with patch("api.main.AsyncSessionLocal", return_value=FakeSessionContext(session)), patch(
            "api.main.execute_http_ping", side_effect=[True, False]
        ), patch("api.main.redis_client", SimpleNamespace(set=redis_set)), patch(
            "api.main.asyncio.sleep", side_effect=stop_after_one_sleep
        ):
            with self.assertRaises(asyncio.CancelledError):
                await continuous_monitoring_loop()

        self.assertEqual(redis_set.await_count, 2)
        self.assertEqual(redis_set.await_args_list[0].args, (f"monitor:status:{http_one.id}", "UP"))
        self.assertEqual(redis_set.await_args_list[1].args, (f"monitor:status:{http_two.id}", "DOWN"))

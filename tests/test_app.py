import sys

import pytest

from conftest import ROOT

sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from storage import MemoryStore  # noqa: E402

ALICE = {"id": "S1", "name": "Alice", "course": "Math"}


@pytest.fixture
def client():
    return create_app(MemoryStore()).test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "storage": "memory"}


def test_add_list_get_count_delete(client):
    assert client.post("/students", json=ALICE).status_code == 201
    assert client.get("/students").get_json() == [ALICE]
    assert client.get("/students/S1").get_json() == ALICE
    assert client.get("/students/count").get_json() == {"count": 1}
    assert client.delete("/students/S1").status_code == 204
    assert client.get("/students/count").get_json() == {"count": 0}


def test_duplicate_id_rejected(client):
    client.post("/students", json=ALICE)
    response = client.post("/students", json=ALICE)
    assert response.status_code == 409


def test_missing_fields(client):
    response = client.post("/students", json={"id": "S2", "name": " "})
    assert response.status_code == 400
    assert "name, course" in response.get_json()["error"]


def test_body_not_json(client):
    response = client.post("/students", data="hello", content_type="text/plain")
    assert response.status_code == 400


def test_unknown_student(client):
    assert client.get("/students/NOPE").status_code == 404
    assert client.delete("/students/NOPE").status_code == 404


def test_health_reports_storage_down():
    class DownStore(MemoryStore):
        name = "redis"

        def ping(self):
            return False

    response = create_app(DownStore()).test_client().get("/health")
    assert response.status_code == 503


def test_redis_target_hides_password():
    from storage import RedisStore

    store = RedisStore("redis://:s3cret@cache.local:6380/1")
    assert store.target == "cache.local:6380/1"
    assert "s3cret" not in store.target

from backend.app import app
import os


def test_health_ok():
    client = app.test_client()
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_ready_has_key():
    client = app.test_client()
    r = client.get('/ready')
    assert r.status_code in (200, 503)
    body = r.get_json()
    assert isinstance(body.get('ready'), bool)

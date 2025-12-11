from backend.app import app
import os


def test_health_ok():
    client = app.test_client()
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_ready_has_key():
    client = app.test_client()
    # Ensure we have a users.json in repository UsersData to expect a 200 ready
    repo_root = os.path.dirname(os.path.dirname(__file__))
    users_json_path = os.path.join(repo_root, 'UsersData', 'users.json')
    os.makedirs(os.path.dirname(users_json_path), exist_ok=True)
    if not os.path.exists(users_json_path):
        with open(users_json_path, 'w', encoding='utf-8') as f:
            f.write('[]')

    r = client.get('/ready')
    assert r.status_code == 200
    body = r.get_json()
    assert body.get('ready') is True

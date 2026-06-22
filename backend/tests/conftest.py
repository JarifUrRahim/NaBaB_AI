"""Shared fixtures for NaBaB backend tests."""
import os
import time
import subprocess
import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ai-bangladesh.preview.emergentagent.com").rstrip("/")
DB_NAME = os.environ.get("DB_NAME", "test_database")


def _mongo_eval(js: str) -> str:
    """Run a mongosh eval and return stdout."""
    res = subprocess.run(
        ["mongosh", DB_NAME, "--quiet", "--eval", js],
        capture_output=True, text=True, timeout=30,
    )
    if res.returncode != 0:
        raise RuntimeError(f"mongosh failed: {res.stderr}")
    return res.stdout.strip()


def _create_session(is_admin: bool = False, credits: int = 1000) -> dict:
    ts = int(time.time() * 1000)
    user_id = f"test-user-{ts}-{'admin' if is_admin else 'usr'}"
    token = f"test_session_{ts}_{'admin' if is_admin else 'usr'}"
    email = f"test.{'admin' if is_admin else 'user'}+{ts}@nabab.test"
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    created = datetime.now(timezone.utc).isoformat()
    js = f"""
    db.users.insertOne({{
      user_id: "{user_id}",
      email: "{email}",
      name: "Test {'Admin' if is_admin else 'User'}",
      picture: "",
      credits: {credits},
      is_admin: {str(is_admin).lower()},
      created_at: "{created}"
    }});
    db.user_sessions.insertOne({{
      user_id: "{user_id}",
      session_token: "{token}",
      expires_at: "{expires}",
      created_at: "{created}"
    }});
    print("OK");
    """
    _mongo_eval(js)
    return {"user_id": user_id, "session_token": token, "email": email}


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def user_session():
    s = _create_session(is_admin=False, credits=1000)
    yield s
    # cleanup
    try:
        _mongo_eval(
            f'db.users.deleteOne({{user_id:"{s["user_id"]}"}}); '
            f'db.user_sessions.deleteOne({{session_token:"{s["session_token"]}"}}); '
            f'db.conversations.deleteMany({{user_id:"{s["user_id"]}"}}); '
            f'db.messages.deleteMany({{user_id:"{s["user_id"]}"}}); '
            f'db.credit_transactions.deleteMany({{user_id:"{s["user_id"]}"}});'
        )
    except Exception:
        pass


@pytest.fixture(scope="session")
def admin_session():
    s = _create_session(is_admin=True, credits=5000)
    yield s
    try:
        _mongo_eval(
            f'db.users.deleteOne({{user_id:"{s["user_id"]}"}}); '
            f'db.user_sessions.deleteOne({{session_token:"{s["session_token"]}"}});'
        )
    except Exception:
        pass


@pytest.fixture
def anon_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def user_client(user_session):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {user_session['session_token']}"})
    return s


@pytest.fixture
def admin_client(admin_session):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {admin_session['session_token']}"})
    return s


@pytest.fixture
def mongo_eval():
    return _mongo_eval

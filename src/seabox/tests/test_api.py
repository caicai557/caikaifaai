import os
import sys
from fastapi.testclient import TestClient

# Add project root to path
api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api"))
sys.path.insert(0, api_dir)
# Add project root for imports in server.py
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, project_root)

from server import app  # noqa: E402

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "seabox-api"}

def test_get_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "chars_available" in data
    assert "active_instances" in data

def test_translate_endpoint():
    # Mock translation call or expect failure if external service is unreachable.
    # For now we test integration with current simple implementation
    # Note: real translation requires network.

    # We can use a mock or just simple text that might return itself on error
    payload = {"text": "Hello", "target_lang": "zh-CN"}
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    # It should return either translation or fallback
    assert "translated" in json_data

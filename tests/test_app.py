import os, sys
import json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app

def test_home():
    client = app.test_client()
    response = client.get("/")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["message"] == "Hello, CI/CD World!"

def test_health():
    client = app.test_client()
    response = client.get("/health")
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data["status"] == "OK"

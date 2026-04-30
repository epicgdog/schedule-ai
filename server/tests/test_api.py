from fastapi.testclient import TestClient
import pytest
import sys
from pathlib import Path

# Add project root and server to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "server"))
sys.path.insert(0, str(PROJECT_ROOT / "sjsu-data-retrival"))

from server.main import app

client = TestClient(app)

def test_get_all_programs():
    """Test the /api/programs endpoint."""
    response = client.get("/api/programs")
    # If the table is missing, this might return 500
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert isinstance(data["data"], list)

def test_get_course_details():
    """Test the /api/course/{course_code} endpoint."""
    # Assuming "CS 46A" exists in the database
    response = client.get("/api/course/CS 46A")
    # If the course doesn't exist, it should be 404
    # If the table is broken, 500
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["course_name"] != ""

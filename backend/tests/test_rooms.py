from datetime import datetime, timezone, timedelta
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.security import create_access_token

client = TestClient(app)

def get_staff_token(role="LE_TAN", username="letan1", user_id=2):
    return create_access_token({
        "sub": str(user_id),
        "username": username,
        "role": role,
        "full_name": f"Test {role}"
    })

def test_room_board_requires_authentication():
    res = client.get("/api/v1/rooms/board")
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"

def test_room_board_forbidden_for_buong_phong():
    token = get_staff_token(role="BUONG_PHONG", username="tapvu1", user_id=4)
    res = client.get("/api/v1/rooms/board", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert res.json()["code"] == "FORBIDDEN"

def test_room_board_success_for_le_tan():
    token = get_staff_token(role="LE_TAN", username="letan1", user_id=2)
    res = client.get("/api/v1/rooms/board", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert "floors" in data
    assert "stats" in data
    assert "at" in data

    floors = data["floors"]
    assert len(floors) == 5

    total_rooms = 0
    for fl in floors:
        assert len(fl["rooms"]) == 10
        total_rooms += len(fl["rooms"])
        for rm in fl["rooms"]:
            assert rm["floor"] == fl["floor"]
            assert rm["status"] in ("TRONG", "DANG_O", "DANG_DON", "BAO_TRI")
            assert rm["roomType"] in ("STANDARD", "SUPERIOR", "DELUXE", "SUITE")

    assert total_rooms == 50
    stats = data["stats"]
    assert stats["total"] == 50
    assert stats["available"] + stats["occupied"] + stats["cleaning"] + stats["maintenance"] == 50

def test_room_board_success_for_quan_ly():
    token = get_staff_token(role="QUAN_LY", username="admin", user_id=1)
    res = client.get("/api/v1/rooms/board", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["floors"]) == 5

def test_room_board_with_specific_at_timestamp():
    token = get_staff_token(role="LE_TAN", username="letan1", user_id=2)
    # Query at a far future date
    future_at = "2029-01-01T12:00:00+07:00"
    res = client.get("/api/v1/rooms/board", params={"at": future_at}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["floors"]) == 5

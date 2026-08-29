from app.models import models
import pytest

@pytest.mark.idols
def test_get_idols_empty(client):
    """client here is the fixture in conftest file and Pytest sees this func asks for a parameter named client, matches it to fixture of same name and runs that then gives a yeilded value"""
    # fixtures are requested by parameter name, not imported or called directly.
    response = client.get("/api/idols/")
    assert response.status_code == 200
    assert (
        response.json()["items"] == []
    )  # uses a freshly created db, so it will get an empty list
    assert response.json()["total"] == 0

@pytest.mark.idols
def test_create_idol_requires_admin(client):
    """client provides a fresh db session as dependency, uses a normal user, so it should not be able to create a new idol"""
    response = client.post(
        "/api/idols/",
        json={"stage_name": "sOmi", "gender": "F"},
    )
    assert response.status_code == 401


@pytest.mark.idols
def test_create_idol_as_admin(
    admin_client, db_session
):  # why are we providing this a db session, but not when it's not an admin??
    """used admin user this time, should be a success. creates a group directly on db instead of going to the group creation route, then inserts an idol in that group"""
    group = models.Group(name="Test Group", slug="test-group")
    db_session.add(group)
    db_session.commit()

    response = admin_client.post(
        "/api/idols/", json={"stage_name": "Somi", "gender": "F", "group_id": group.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stage_name"] == "Somi"
    assert data["id"] is not None


@pytest.mark.idols
def test_create_duplicate_idol_conflict(admin_client, db_session):
    """uses same payload for 2 idol creation and it should raise a conflict error"""

    #  creates a group directly on db instead of going to the group creation route, then inserts an idol in that group
    group = models.Group(name="Test Group", slug="test-group")
    db_session.add(group)
    db_session.commit()

    payload = {"stage_name": "Somi", "gender": "F", "group_id": group.id}
    first = admin_client.post(
        "/api/idols/",
        json=payload,
    )
    assert first.status_code == 200
    second = admin_client.post(
        "/api/idols/",
        json=payload,
    )
    assert second.status_code == 409


@pytest.mark.idols
@pytest.mark.parametrize("bad_limit", [-1, 0, 101])
def test_get_idols_rejects_invalid_limit(client, bad_limit):
    """uses out of range limits, multiple times. each of them should get status code 422"""
    response = client.get(f"/api/idols/?limit={bad_limit}")
    assert response.status_code == 422

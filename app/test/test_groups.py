from app.models import models
import pytest


@pytest.mark.groups
def test_get_groups_empty(client):
    """Tests if it gets empty list for no groups"""
    response = client.get("/api/groups/")
    assert response.status_code == 200
    assert (
        response.json()["items"]
        == []
        # uses a fresh db, so no groups -> empty list
    )
    assert response.json()["total"] == 0


@pytest.mark.groups
def test_create_group_requires_admin(client):
    """uses a normal user for creating a group, will get 401"""
    response = client.post(
        "/api/groups/",
        json={"name": "idle"},
    )
    assert response.status_code == 401


@pytest.mark.groups
def test_create_group_as_admin(admin_client, db_session):
    """uses admin client to create group this time, should be a 200"""

    response = admin_client.post(
        "/api/groups/",
        json={"name": "I-DLE"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "I-DLE"
    assert response.json()["id"] is not None


@pytest.mark.groups
def test_create_duplicate_group_conflict(admin_client, db_session):
    """uses same payload for 2 group creation and it should raise a conflict error"""
    payload = {"name": "I-DLE"}
    first_group = admin_client.post(
        "/api/groups/",
        json=payload,
    )
    assert first_group.status_code==200
    second_group = admin_client.post(
        "/api/groups/",
        json=payload,
    )
    assert second_group.status_code==409



@pytest.mark.groups
@pytest.mark.parametrize("bad_limit", [-1, 0, 101])
def test_get_groups_rejects_invalid_limit(client, bad_limit):
    """uses out of range limits, multiple times. each of them should get status code 422"""
    response = client.get(f"/api/groups/?limit={bad_limit}")
    assert response.status_code == 422

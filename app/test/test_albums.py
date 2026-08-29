from conftest import (
    client,
)  # provides a db session from fresh db instead of production db
from app.models import models
import pytest


@pytest.mark.albums
def tesst_get_albums(client):
    """Tests if it gets empty list for no albums"""
    response = client.get("/api/albums/")
    assert response.status_code == 200
    assert response.json()["items"] == []  # uses a fresh db, so no albums -> empty list
    assert response.json()["total"] == 0


@pytest.mark.albums
def test_create_albums_requires_admin(client):
    """uses normal user to create an album, should get a 401"""
    response = client.post("/api/albums/", json={"name": "Once Begins, Twice Ends"})
    assert response.status_code == 401


@pytest.mark.albums
def test_create_albums_as_admin(admin_client):
    """uses admin client to create album this time, should be a 200"""

    response = admin_client.post(
        "/api/albums/", json={"name": "Once Begins, Twice Ends"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Once Begins, Twice Ends"
    assert response.json()["id"] is not None


@pytest.mark.albums
def test_create_duplicate_group_conflict(admin_client, db_session):
    """uses same payload for 2 album creation and it should raise a conflict error"""
    payload = {"name": "Once Begins, Twice Ends"}
    first_album = admin_client.post(
        "/api/albums/",
        json=payload,
    )
    assert first_album.status_code == 200
    second_album = admin_client.post(
        "/api/albums/",
        json=payload,
    )
    assert second_album.status_code == 409


@pytest.mark.albums
@pytest.mark.parametrize("bad_limit", [-1, 0, 101])
def test_get_albums_rejects_invalid_limit(client, bad_limit):
    """uses out of range limits, multiple times. each of them should get status code 422"""
    response = client.get(f"/api/albums/?limit={bad_limit}")
    assert response.status_code == 422

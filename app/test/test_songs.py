import pytest
from app.models import models


@pytest.mark.songs
def test_get_songs_empty(client):
    """Tests if it gets empty list for no songs"""
    response = client.get("/api/songs/")
    assert response.status_code == 200
    assert (
        response.json()["items"]
        == []
        # uses a fresh db, so no songs -> empty list
    )
    assert response.json()["total"] == 0


@pytest.mark.songs
def test_create_songs_requires_admin(client, db_session):
    """uses a normal user for creating a group, will get 401"""
    # create album first, song can not be created without album id
    album = models.Album(
        name="New album",
        slug="new-album",
    )
    db_session.add(album)
    db_session.commit()

    response = client.post(
        "/api/songs/",
        json={
            "title": "Test Title",
            "album_id": album.id,
        },
    )

    assert response.status_code == 401


@pytest.mark.songs
def test_create_album_as_admin(admin_client, db_session):
    """uses admin client to create album this time, should be a 200"""

    # create album first, song can not be created without album id
    album = models.Album(
        name="New album",
        slug="new-album",
    )
    db_session.add(album)
    db_session.commit()

    response = admin_client.post(
        "/api/songs/",
        json={
            "title": "Test Title",
            "album_id": album.id,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Test Title"
    assert response.json()["id"] is not None


@pytest.mark.songs
def test_create_duplicate_songs_conflict(admin_client, db_session):
    """uses same payload for 2 album creation and it should raise a conflict error"""

    # create album first, song can not be created without album id
    album = models.Album(
        name="New album",
        slug="new-album",
    )
    db_session.add(album)
    db_session.commit()

    payload = (
        {
            "title": "Test Title",
            "album_id": album.id
        }
    )
    first_song = admin_client.post(
        "/api/songs/",
        json=payload,
    )
    assert first_song.status_code == 200
    second_song = admin_client.post(
        "/api/songs/",
        json=payload,
    )
    assert second_song.status_code == 409


@pytest.mark.songs
@pytest.mark.parametrize("bad_limit", [-1, 0, 101])
def test_get_albums_rejects_invalid_limit(client, bad_limit):
    """uses out of range limits, multiple times. each of them should get status code 422"""
    response = client.get(f"/api/songs/?limit={bad_limit}")
    assert response.status_code == 422

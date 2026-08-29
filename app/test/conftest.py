import os

os.environ["TESTING"] = "True"

# This is a special pytest filename — pytest automatically finds and loads it, making everything defined here (called fixtures) available to every test file in that folder, without importing anything manually.
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient


from app.database.database import Base, get_db
from app.src.main import app
from app.models import models
from app.config.config import settings
from app.security.password import hash_password
from app.config.enums import UserRole

engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


# a reusable setup/teardown block, and the yield inside it is the key mechanic.
# Everything before yield runs as setup, before your test executes
# Everything after yield runs as teardown, after your test finishes — regardless of whether the test passed or failed.


@pytest.fixture
def db_session():
    """Builds every table fresh and hands the test a working session, once test is done, closes the session and wipes every table, ensuring every single test starts from a completely clean, empty database"""
    Base.metadata.create_all(bind=engine)  # build every table on test db

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)  # unhook everything after test


@pytest.fixture
def client(db_session):
    def override_get_db():
        """dependency_overrides is FastAPI's built-in mechanism to say "whenever any route asks for get_db, secretly give it override_get_db instead, just for this test run"""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Takes a fresh db, inserts a new User"""
    user = models.User(
        username="admin_test",
        email="admin@test.com",
        hashed_password=hash_password("testpassword123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_client(client, admin_user):
    """uses admin user so that before login, the user exists in db and calls actual login route to log in"""
    response = client.post(
        "/api/users/login",
        data={
            "username": "admin_test",
            "password": "testpassword123",
        },
    )
    token = response.json()["access_token"]
    # print(f"\nPrint from admin client testing :{response}\n")

    # print("STATUS:", response.status_code)
    # print("BODY:", response.json())
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client

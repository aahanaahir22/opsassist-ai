import os

os.environ["OPSASSIST_DATABASE_URL"] = "sqlite:///./test_opsassist.db"
os.environ["OPSASSIST_SEED_DEMO"] = "false"
import pytest
from app.database import Base, engine
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as value:
        yield value

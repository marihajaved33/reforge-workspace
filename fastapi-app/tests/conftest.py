import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from main import app
from db.database import Base, get_db


@pytest.fixture(scope="function")
def client():
    # StaticPool forces all sessions to share the same in-memory connection,
    # so tables created in create_all() are visible to every subsequent session.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()

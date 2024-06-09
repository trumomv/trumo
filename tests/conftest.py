import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from models.base_model import Base
from pydantic_models.user import UserCreate
from services.user_service import UserService

# Use a separate database for testing
test_database_url = "postgresql://postgres:password@db:5432/trumo_tests"
engine = create_engine(test_database_url)
if not database_exists(engine.url):
    # If not, create it
    create_database(engine.url)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def session():

    try:
        db = TestingSessionLocal()
        db.begin()
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    # Setup: Clear the database before each test
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # Yield to run the test
    yield
    # Teardown: Close the database session


@pytest.fixture(scope="function")
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("session")
def create_user(session):
    def _create_user(name: str, balance: Decimal):
        user_data = {"name": name, "balance": balance}
        user_create = UserCreate(**user_data)
        user = UserService.create_user(session, user_create)
        session.commit()
        return user

    return _create_user

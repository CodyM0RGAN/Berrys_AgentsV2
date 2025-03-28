"""
Pytest configuration file for Project Coordinator tests.

This file contains fixtures and configuration for the tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.dependencies import get_db
from src.models.internal import Base
from shared.utils.src.db_connection import get_sync_database_url


# Set environment to test if not already set
if "ENVIRONMENT" not in os.environ:
    os.environ["ENVIRONMENT"] = "test"

# Get database URL for the test environment
# When running tests locally, use localhost instead of postgres
db_host = "localhost" if os.environ.get("CI") != "true" else "postgres"
SQLALCHEMY_DATABASE_URL = get_sync_database_url(host=db_host)

# Create engine and session factory
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for a test.
    
    This fixture creates a transaction that is rolled back after the test,
    ensuring that tests don't affect each other.
    """
    # Connect to the database
    connection = engine.connect()
    
    # Begin a transaction
    transaction = connection.begin()
    
    # Create a session bound to the connection
    db = TestingSessionLocal(bind=connection)
    
    try:
        yield db
    finally:
        db.close()
        # Roll back the transaction
        transaction.rollback()
        # Close the connection
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client for the FastAPI app.
    
    This fixture overrides the get_db dependency to use the test database session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Reset the dependency override
    app.dependency_overrides = {}

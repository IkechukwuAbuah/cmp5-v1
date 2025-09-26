"""Test configuration and fixtures for the EFL Agent Assistant API."""

import pytest
from fastapi.testclient import TestClient

from src.main import create_application


@pytest.fixture(scope="session")
def app():
    """Create and configure the FastAPI test application."""
    return create_application()


@pytest.fixture(scope="session")
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Setup code here (if needed)
    yield
    # Teardown code here (if needed)

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from src.app import app

# Configure pytest-asyncio to use function scope for event loop
pytest_asyncio.fixture_scope = "function"

@pytest_asyncio.fixture(scope="function")
async def client():
    """Basic async HTTP client for testing."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def admin_user_token(client):
    """Create admin user and return auth token."""

    # Register admin user
    emp_id = "TEST_ADMIN"
    password = "admin123"
    
    await client.post("/auth/register", json={
        "employee_id": emp_id,
        "password": password,
        "role": "admin"
    })
    
    # Login and get token
    r = await client.post("/auth/login", json={
        "employee_id": emp_id,
        "password": password
    })
    
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None

@pytest_asyncio.fixture(scope="function") 
async def simple_user_token(client):
    """Create simple user and return auth token."""

    # Register simple user
    emp_id = "TEST_SIMPLE"
    password = "simple123"
    
    await client.post("/auth/register", json={
        "employee_id": emp_id,
        "password": password,
        "role": "simple"
    })
    
    # Login and get token
    r = await client.post("/auth/login", json={
        "employee_id": emp_id,
        "password": password
    })
    
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None

@pytest.fixture(autouse=True)
def isolate_db():
    """Ensure database isolation between tests."""

    # This is a placeholder for database isolation
    # In a real scenario, you might want to use database transactions
    # or separate test databases
    pass
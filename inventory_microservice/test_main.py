#While the above fix will solve the NameError, you are currently 
# running your tests against your main development database (store.db). 
# This is a bad practice because:

# Your tests will leave leftover data in your development DB.
# If you have existing data, it could cause your tests to fail unpredictably.
# Tests should always run in a clean, isolated, and repeatable environment.
# The professional way to handle this in FastAPI is to override the database dependency during testing.

# Here is the updated, complete, and much better test_main.py that fixes the NameError and isolates the database.

import pytest  # to test the code with one single command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, Base, get_db # Import the original get_db dependency

# --- Test Database Setup ---
# Use an in-memory SQLite database or a separate file for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables in the test database
Base.metadata.create_all(bind=engine)

# --- Dependency Override ---
# This function will replace the `get_db` function in `main.py` during tests
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Tell the app to use our new `override_get_db` for any test that runs
app.dependency_overrides[get_db] = override_get_db


# --- Test Client ---
client = TestClient(app)


# --- Tests ---

def test_order_creation_and_stock_reduction():
    # 1. Create a product with known stock in the clean test DB
    response = client.post(
        "/products",
        json={"name": "Test Monitor", "price": 300, "stock": 10},
    )
    assert response.status_code == 201
    product = response.json()
    product_id = product["id"]

    # 2. Create a valid order
    response = client.post(
        "/orders", json={"product_id": product_id, "quantity": 3}
    )
    assert response.status_code == 201

    # 3. Verify stock has been reduced
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["stock"] == 7  # 10 - 3 = 7

def test_insufficient_stock_error():
    # 1. Create a product with low stock
    response = client.post(
        "/products",
        json={"name": "Test Speakers", "price": 150, "stock": 2},
    )
    assert response.status_code == 201
    product_id = response.json()["id"]

    # 2. Try to order more than available stock
    response = client.post(
        "/orders", json={"product_id": product_id, "quantity": 5}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient stock"



    # Why this new version is better:

# Imports Correctly: It fixes the NameError by importing sessionmaker.
# Creates a Test Database: It creates a new, separate database file named 
# test.db that will only be used for testing.
# Overrides Dependency: The line app.dependency_overrides[get_db] = override_get_db
#  is the magic. It tells FastAPI: "Whenever a route asks for a database 
# session by calling get_db, don't run the original function. 
# Instead, run my override_get_db function."
# Isolated Tests: Your tests are now completely separate from your development
#  data, making them reliable and clean. You can delete test.db at any time 
# without affecting your store.db.

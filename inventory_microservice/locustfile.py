# locustfile.py
from locust import HttpUser, task, between

class StoreUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    product_id = 1 # Assume we are testing with product 1

    @task
    def get_product(self):
        self.client.get(f"/products/{self.product_id}")

    @task(3) # Make this task 3 times more likely
    def create_order(self):
        # To run a load test without depleting stock, you'd mock the DB
        # or have a dedicated testing endpoint. For this demo, we'll hit the real one.
        payload = {"product_id": self.product_id, "quantity": 1}
        self.client.post("/orders", json=payload)
        
    def on_start(self):
        # Create a product to test against when the user starts
        self.client.post("/products", json={"name": "Locust Test Product", "price": 10, "stock": 9999})
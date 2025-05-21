import random
import json
from locust import HttpUser, task, between, events
from requests.exceptions import JSONDecodeError

def random_email():
    return f"locust_{random.randint(1,10_000)}@example.com"

class BaseUser(HttpUser):
    abstract = True
    host = "http://35.205.113.202:3000"
    wait_time = between(1, 3)

    def on_start(self):
        # register/login so subclasses inherit auth
        self.email = random_email()
        self.password = "Passw0rd!"
        self.client.post("/api/register", json={
            "name": "LocustUser",
            "email": self.email,
            "password": self.password
        })
        self.client.post("/api/login", json={
            "email": self.email,
            "password": self.password
        })

class WebsiteUser(BaseUser):
    weight = 1  # half the users

    @task(2)
    def load_homepage(self):
        self.client.get("/", name="homepage")

    @task(3)
    def list_and_view_product(self):
        with self.client.get("/api/products", name="/api/products", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"list_products: Expected 200, got {resp.status_code}")
                return
            try:
                products = resp.json()
            except JSONDecodeError:
                resp.failure(f"list_products: Invalid JSON: {resp.text[:200]!r}")
                return

        pid = random.choice(products)["id"]
        self.client.get(f"/products/{pid}", name="view_product")

    @task(1)
    def wishlist_flow(self):
        with self.client.get("/api/products", name="/api/products", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"wishlist_flow: Expected 200, got {resp.status_code}")
                return
            try:
                products = resp.json()
            except JSONDecodeError:
                resp.failure(f"wishlist_flow: Invalid JSON: {resp.text[:200]!r}")
                return

        pid = random.choice(products)["id"]
        self.client.get(f"/products/{pid}", name="view_product")
        self.client.post("/api/wishlist", json={"productId": pid}, name="/api/wishlist")
        self.client.get("/wishlist", name="view_wishlist")
        self.client.delete(f"/api/wishlist/{pid}", name="/api/wishlist/[id]")

    @task(1)
    def checkout_and_review(self):
        with self.client.get("/api/products", name="/api/products", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"checkout_products: Expected 200, got {resp.status_code}")
                return
            try:
                products = resp.json()
            except JSONDecodeError:
                resp.failure(f"checkout_products: Invalid JSON: {resp.text[:200]!r}")
                return

        item = random.choice(products)
        pid = item["id"]

        self.client.get(f"/products/{pid}", name="view_product")
        self.client.get("/checkout", name="view_checkout")

        cart = [{"id": pid, "quantity": 1, "price": item.get("price") or 1}]
        payment_payload = {
            "cardNumber": "4111111111111111",
            "expiry":     "12/30",
            "cvv":        "123",
            "cart":       cart,
            "address":    "123 Main St"
        }

        with self.client.post("/api/payment", json=payment_payload, name="/api/payment", catch_response=True) as pay_resp:
            if pay_resp.status_code != 200:
                pay_resp.failure(f"payment: Expected 200, got {pay_resp.status_code}")
                return

        self.client.get("/order-confirmation", name="view_order_confirmation")

        # leave a review
        self.client.get(f"/products/{pid}", name="view_product")
        rating = random.randint(1,5)
        self.client.post("/api/ratings", json={
            "productId": pid,
            "rating":    rating
        }, name="/api/ratings")
        self.client.post("/api/comments", json={
            "productId":    pid,
            "comment_text": f"Locust automated review — {rating} stars!"
        }, name="/api/comments")

class DashboardUser(BaseUser):
    weight = 1  # the other half

    @task(5)
    def view_dashboard(self):
        self.client.get("/dashboard", name="dashboard")

    @task(1)
    def occasional_product_view(self):
        with self.client.get("/api/products", name="/api/products", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"dash_product_list: Expected 200, got {resp.status_code}")
                return
            try:
                products = resp.json()
            except JSONDecodeError:
                resp.failure(f"dash_product_list: Invalid JSON: {resp.text[:200]!r}")
                return

        pid = random.choice(products)["id"]
        self.client.get(f"/products/{pid}", name="dash_view_product")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n--- Locust run complete ---")

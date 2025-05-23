import random
import json
from locust import HttpUser, task, between, events
from requests.exceptions import JSONDecodeError

# Funnel ratios
REGISTER_PROB = 0.25  # 25% of users register/login
BROWSE_PROB = 0.50    # 50% of users view products
PURCHASE_PROB = 0.03  # 3% of users complete a purchase
REVIEW_PROB = 0.30    # 30% of purchasers leave a review

# Maximum of 7 products (IDs 1–7)
MAX_PRODUCTS = 7

# Personalized review templates
REVIEW_TEMPLATES = [
    "Absolutely love this product!",
    "Pretty decent, does the job.",
    "Exceeded my expectations!",
    "Not what I expected, but okay.",
    "Could be better, but worth the price.",
    "Five stars! Will buy again.",
    "Terrible quality, do not buy!",
    "Solid purchase, highly recommend."
]

def random_email():
    return f"locust_{random.randint(1,10_000)}@example.com"

class EcommerceUser(HttpUser):
    host = "http://35.190.215.149:3000"
    wait_time = between(1, 3)

    def on_start(self):
        # everyone lands on homepage
        self.client.get("/", name="dashboard")
        # decide if user will register/login
        self.is_registered = random.random() < REGISTER_PROB
        if self.is_registered:
            email = random_email()
            password = "Passw0rd!"
            self.client.post("/api/register", json={"name": "LocustUser", "email": email, "password": password})
            self.client.post("/api/login", json={"email": email, "password": password})

    @task(50)
    def browse_products(self):
        """
        ~50% of users browse products after visiting homepage
        """
        self.client.get("/", name="dashboard")
        if random.random() > BROWSE_PROB:
            return
        with self.client.get("/api/products", name="/api/products", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"list_products: Expected 200, got {resp.status_code}")
                return
            try:
                products = resp.json()
            except JSONDecodeError:
                resp.failure(f"list_products: Invalid JSON: {resp.text[:200]!r}")
                return
        pid = random.choice(products).get("id") if products else random.randint(1, MAX_PRODUCTS)
        self.client.get(f"/product-page/{pid}", name="view_product")

    @task(25)
    def view_dashboard(self):
        """
        ~25% weight for homepage visits
        """
        self.client.get("/", name="dashboard")

    @task(3)
    def purchase_flow(self):
        """
        ~3% of users complete a purchase. Reviews are separate.
        """
        self.client.get("/", name="dashboard")
        if random.random() > PURCHASE_PROB:
            return
        # fetch and pick product
        with self.client.get("/api/products", name="/api/products", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"checkout_products: Expected 200, got {resp.status_code}")
                return
            try:
                products = resp.json()
            except JSONDecodeError:
                resp.failure(f"checkout_products: Invalid JSON: {resp.text[:200]!r}")
                return
        item = random.choice(products) if products else {"id": random.randint(1, MAX_PRODUCTS), "price": 1}
        pid = item.get("id")
        # checkout sequence
        self.client.get(f"/product-page/{pid}", name="view_product")
        self.client.get("/payment", name="checkout_page")
        cart = [{"id": pid, "quantity": 1, "price": item.get("price") or 1}]
        payload = {"cardNumber": "4111111111111111", "expiry": "12/30", "cvv": "123", "cart": cart, "address": "123 Main St"}
        with self.client.post("/api/payment", json=payload, name="payment_api", catch_response=True) as pay_resp:
            if pay_resp.status_code != 200:
                pay_resp.failure(f"payment: Expected 200, got {pay_resp.status_code}")
                return
            try:
                invoice_id = pay_resp.json().get("invoice_id")
            except JSONDecodeError:
                invoice_id = None
        # view invoice
        self.client.get(f"/invoice/{invoice_id or 1}", name="view_invoice")
        # after purchase, decide on review
        if random.random() < REVIEW_PROB:
            self._leave_review(pid)

    def _leave_review(self, pid):
        """
        Internal: posts a rating + comment for given product id
        """
        self.client.get(f"/product-page/{pid}", name="view_product")
        rating = random.randint(1, 5)
        comment = random.choice(REVIEW_TEMPLATES)
        full_comment = f"{comment} ({rating} stars)"
        self.client.post("/api/ratings", json={"productId": pid, "rating": rating}, name="api_ratings")
        self.client.post("/api/comments", json={"productId": pid, "comment_text": full_comment}, name="api_comments")

@events.test_stop.add_listener

def on_test_stop(environment, **kwargs):
    print("\n--- Locust run complete ---")

"""User acceptance testing simulation script for API-driven commerce demo."""

from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse, urlunparse

import requests


DEFAULT_USERS = [
    {"email": "user1@example.com", "password": "pass123", "full_name": "Demo User 1"},
    {"email": "user2@example.com", "password": "pass123", "full_name": "Demo User 2"},
    {"email": "user3@example.com", "password": "pass123", "full_name": "Demo User 3"},
]


@dataclass
class APIClient:
    base_url: str
    session: requests.Session
    token: str | None = None

    def _url(self, path: str) -> str:
        base = self.base_url.rstrip('/')
        suffix = path if path.startswith('/') else f"/{path}"
        return f"{base}{suffix}"

    def request(self, method: str, path: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.session.request(method, self._url(path), headers=headers, timeout=15, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError:
            pass
        return response.text

    def register(self, email: str, password: str, full_name: str | None = None, *, is_admin: bool = False):
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "is_admin": is_admin,
        }
        try:
            self.request("POST", "/auth/register", json=payload)
        except requests.HTTPError as exc:  # allow already registered users
            if exc.response is None or exc.response.status_code != 400:
                raise

    def login(self, email: str, password: str):
        payload = {"email": email, "password": password}
        data = self.request("POST", "/auth/login", json=payload)
        self.token = data["access_token"]

    def list_products(self):
        return self.request("GET", "/products")

    def add_to_cart(self, product_id: int, quantity: int = 1):
        return self.request("POST", "/cart/items", json={"product_id": product_id, "quantity": quantity})

    def view_cart(self):
        return self.request("GET", "/cart")

    def checkout(self):
        return self.request("POST", "/orders", json={})


def simulate_user(client: APIClient, email: str, password: str, full_name: str | None, *, cart_actions: int) -> None:
    client.register(email, password, full_name)
    client.login(email, password)
    products = client.list_products()
    available = [p for p in products if int(p.get("inventory_count", 0) or 0) > 0]
    if not available:
        raise RuntimeError("No products with inventory available for cart simulation")
    for _ in range(cart_actions):
        product = random.choice(available)
        max_qty = int(product.get("inventory_count", 1) or 1)
        quantity = random.randint(1, min(2, max_qty))
        try:
            client.add_to_cart(product_id=product["id"], quantity=quantity)
            product["inventory_count"] = max(int(product.get("inventory_count", 0)) - quantity, 0)
            if int(product["inventory_count"]) <= 0:
                available = [p for p in available if p.get("id") != product["id"]]
                if not available:
                    break
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                print(f"  Skipping product {product['name']}: {exc.response.json().get('detail')}")
                available = [p for p in client.list_products() if int(p.get("inventory_count", 0) or 0) > 0]
                if not available:
                    break
                continue
            raise
    cart = client.view_cart()
    print(f"Cart for {email}: {len(cart['items'])} items, subtotal {cart['subtotal']}")
    order = client.checkout()
    print(f"Placed order {order['id']} with total {order['total_amount']}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate user flows against the API commerce demo")
    parser.add_argument("--base-url", default="http://shop.fastlylab.com/api", help="Base API URL")
    parser.add_argument("--iterations", type=int, default=1, help="Number of simulation loops to run")
    parser.add_argument("--users", type=int, default=3, help="Number of users to simulate (1-3)")
    parser.add_argument("--cart-actions", type=int, default=2, help="Number of items each user adds before checkout")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between iterations in seconds")
    return parser.parse_args(list(argv))


def normalize_base_url(url: str) -> str:
    """Ensure the base URL includes an API path segment."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path or path == "":
        path = "/api"
    elif path == "/":
        path = "/api"
    elif not path.startswith("/"):
        path = f"/{path}"
    normalized = parsed._replace(path=path)
    return urlunparse(normalized)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    args.base_url = normalize_base_url(args.base_url)
    users = DEFAULT_USERS[: max(1, min(args.users, len(DEFAULT_USERS)))]
    for iteration in range(1, args.iterations + 1):
        print(f"\nIteration {iteration}/{args.iterations}")
        for user in users:
            session = requests.Session()
            client = APIClient(base_url=args.base_url, session=session)
            try:
                simulate_user(client, user["email"], user["password"], user.get("full_name"), cart_actions=args.cart_actions)
            except Exception as exc:  # broad catch for UAT logging
                print(f"User {user['email']} flow failed: {exc}")
            finally:
                session.close()
        if iteration != args.iterations and args.delay > 0:
            time.sleep(args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""User acceptance testing simulation script for API-driven commerce demo."""

from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Iterable, Tuple
from urllib.parse import urlparse, urlunparse
from uuid import uuid4

import requests


DEFAULT_USERS = [
    {"email": "user1@example.com", "password": "pass123", "full_name": "Demo User 1"},
    {"email": "user2@example.com", "password": "pass123", "full_name": "Demo User 2"},
    {"email": "user3@example.com", "password": "pass123", "full_name": "Demo User 3"},
]


DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
]

LANGUAGE_HEADERS = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "en-US,en;q=0.9,fr;q=0.6",
]


@dataclass
class TrafficProfile:
    headers: dict[str, str]
    cookies: dict[str, str]
    cookie_domain: str
    trace_id: str


@dataclass
class APIClient:
    base_url: str
    session: requests.Session
    default_headers: dict[str, str] = field(default_factory=dict)
    trace_id: str | None = None
    token: str | None = None

    def _url(self, path: str) -> str:
        base = self.base_url.rstrip('/')
        suffix = path if path.startswith('/') else f"/{path}"
        return f"{base}{suffix}"

    def request(self, method: str, path: str, **kwargs):
        headers = {**self.default_headers}
        headers.update(kwargs.pop("headers", {}))
        headers.setdefault("Accept", "application/json")
        headers.setdefault("X-Request-ID", uuid4().hex)
        if self.trace_id:
            headers.setdefault("X-Correlation-ID", self.trace_id)
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


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected a positive integer, got '{value}'") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("Value must be at least 1")
    return parsed


def _quantity_override_arg(value: str) -> Tuple[str, int]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Expected KEY=QTY format for --product-quantity")
    key, qty_text = value.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("Quantity override key must not be empty")
    try:
        quantity = int(qty_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid quantity '{qty_text}' for {key}") from exc
    if quantity < 1:
        raise argparse.ArgumentTypeError("Quantity overrides must be at least 1")
    return key, quantity


def _random_ip() -> str:
    octets = [str(random.randint(11, 240)) for _ in range(4)]
    return ".".join(octets)


def _build_traffic_profile(base_url: str, user_email: str) -> TrafficProfile:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc or parsed.path}"
    referer_paths = [
        "/app",
        "/app/products",
        "/app/cart",
        "/app/checkout",
    ]
    device_type = random.choice(["desktop", "mobile"])
    user_agents = DESKTOP_USER_AGENTS if device_type == "desktop" else MOBILE_USER_AGENTS
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": random.choice(LANGUAGE_HEADERS),
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
        "Origin": origin,
        "Referer": f"{origin}{random.choice(referer_paths)}",
        "X-Forwarded-For": _random_ip(),
        "X-Real-IP": _random_ip(),
        "X-Device-Id": uuid4().hex,
        "X-Session-Id": uuid4().hex,
        "X-Channel": random.choice(["web", "mobile-web", "affiliate", "retargeting"]),
        "X-Requested-With": "XMLHttpRequest",
    }
    cookies = {
        "session_id": uuid4().hex,
        "ab_bucket": random.choice(["A", "B"]),
        "preferred_currency": random.choice(["USD", "EUR", "GBP"]),
        "remember_email": user_email,
    }
    cookie_domain = parsed.hostname or (parsed.netloc.split(":")[0] if ":" in parsed.netloc else parsed.netloc)
    return TrafficProfile(headers=headers, cookies=cookies, cookie_domain=cookie_domain, trace_id=uuid4().hex)


def simulate_user(
    client: APIClient,
    email: str,
    password: str,
    full_name: str | None,
    *,
    cart_actions: int,
    purchase_mode: str,
    default_product_quantity: int,
    quantity_overrides: dict[str, int],
) -> None:
    client.register(email, password, full_name)
    client.login(email, password)
    products = client.list_products()
    available = [p for p in products if int(p.get("inventory_count", 0) or 0) > 0]
    if not available:
        raise RuntimeError("No products with inventory available for cart simulation")
    if purchase_mode == "all":
        overrides_by_id: dict[int, int] = {}
        overrides_by_name: dict[str, int] = {}
        for key, quantity in quantity_overrides.items():
            if key.isdigit():
                overrides_by_id[int(key)] = quantity
            else:
                overrides_by_name[key.lower()] = quantity
        for product in available:
            product_id = product.get("id")
            available_inventory = int(product.get("inventory_count", 0) or 0)
            if available_inventory <= 0:
                continue
            quantity = None
            if isinstance(product_id, int) and product_id in overrides_by_id:
                quantity = overrides_by_id[product_id]
            else:
                name = str(product.get("name", ""))
                if name and name.lower() in overrides_by_name:
                    quantity = overrides_by_name[name.lower()]
            if quantity is None:
                quantity = default_product_quantity
            if quantity <= 0:
                continue
            if quantity > available_inventory:
                quantity = available_inventory
            try:
                client.add_to_cart(product_id=product_id, quantity=quantity)
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 400:
                    error_detail = exc.response.json().get("detail")
                    print(f"  Skipping product {product.get('name', product_id)}: {error_detail}")
                    continue
                raise
    else:
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
    total_quantity = sum(item.get("quantity", 0) for item in cart.get("items", []))
    print(f"Cart for {email}: {total_quantity} items, subtotal {cart['subtotal']}")
    order = client.checkout()
    print(f"Placed order {order['id']} with total {order['total_amount']}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate user flows against the API commerce demo")
    parser.add_argument("--base-url", default="http://shop.exampledomain.com/api", help="Base API URL")
    parser.add_argument("--iterations", type=int, default=1, help="Number of simulation loops to run")
    parser.add_argument("--users", type=int, default=3, help="Number of users to simulate (1-3)")
    parser.add_argument("--cart-actions", type=int, default=2, help="Number of items each user adds before checkout in random mode")
    parser.add_argument(
        "--purchase-mode",
        choices=("random", "all"),
        default="random",
        help="random: add items randomly (default); all: add every available product",
    )
    parser.add_argument(
        "--default-product-quantity",
        type=_positive_int,
        default=1,
        help="Quantity to add for each product when using purchase-mode=all",
    )
    parser.add_argument(
        "--product-quantity",
        dest="product_quantities",
        action="append",
        type=_quantity_override_arg,
        metavar="KEY=QTY",
        help="Override quantity for a product in purchase-mode=all using product id or name",
    )
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
            profile = _build_traffic_profile(args.base_url, user["email"])
            session.headers.update(
                {k: v for k, v in profile.headers.items() if k in {"User-Agent", "Accept-Language", "Accept-Encoding"}}
            )
            for cookie_name, cookie_value in profile.cookies.items():
                session.cookies.set(cookie_name, cookie_value, domain=profile.cookie_domain, path="/")
            client = APIClient(
                base_url=args.base_url,
                session=session,
                default_headers=profile.headers,
                trace_id=profile.trace_id,
            )
            try:
                simulate_user(
                    client,
                    user["email"],
                    user["password"],
                    user.get("full_name"),
                    cart_actions=args.cart_actions,
                    purchase_mode=args.purchase_mode,
                    default_product_quantity=args.default_product_quantity,
                    quantity_overrides={key: qty for key, qty in args.product_quantities or []},
                )
            except Exception as exc:  # broad catch for UAT logging
                print(f"User {user['email']} flow failed: {exc}")
            finally:
                session.close()
        if iteration != args.iterations and args.delay > 0:
            time.sleep(args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

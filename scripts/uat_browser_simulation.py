"""Headless browser UAT simulator using Playwright to bypass bot challenges."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

from playwright.async_api import async_playwright


DEFAULT_USERS = [
    {"email": "user1@example.com", "password": "pass123", "full_name": "Demo User 1"},
    {"email": "user2@example.com", "password": "pass123", "full_name": "Demo User 2"},
    {"email": "user3@example.com", "password": "pass123", "full_name": "Demo User 3"},
]


@dataclass
class APIResult:
    status: int
    ok: bool
    data: object


async def api_request(page, base_api: str, path: str, *, method: str = "GET", token: str | None = None, body: dict | None = None) -> APIResult:
    payload = json.dumps(body) if body is not None else None
    result = await page.evaluate(
        """
        async ({ method, url, token, payload }) => {
          const headers = { Accept: 'application/json' };
          if (payload !== null) {
            headers['Content-Type'] = 'application/json';
          }
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          const response = await fetch(url, {
            method,
            headers,
            body: payload === null ? undefined : payload,
          });
          const text = await response.text();
          let data;
          try {
            data = JSON.parse(text);
          } catch (err) {
            data = text;
          }
          return {
            status: response.status,
            ok: response.ok,
            data,
          };
        }
        """,
        {
            "method": method,
            "url": f"{base_api.rstrip('/')}{path}",
            "token": token,
            "payload": payload,
        },
    )
    return APIResult(**result)


async def wait_for_edge_challenge(page, base_api: str, timeout: int = 60000) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + (timeout / 1000)
    while True:
        if loop.time() > deadline:
            raise RuntimeError("Timed out waiting for edge challenge to complete")
        probe = await api_request(page, base_api, "/products")
        if probe.ok and isinstance(probe.data, list):
            return
        await asyncio.sleep(1.5)


async def ensure_pow_cookie(page, base_api: str, token: str | None = None) -> None:
    probe = await api_request(page, base_api, "/products", token=token)
    if not probe.ok:
        detail = probe.data if isinstance(probe.data, str) else probe.data.get("detail")
        raise RuntimeError(f"Pre-flight challenge failed: {detail}")


async def simulate_user(page, base_api: str, user: dict, *, cart_actions: int) -> None:
    await ensure_pow_cookie(page, base_api)

    register_payload = {
        "email": user["email"],
        "password": user["password"],
        "full_name": user.get("full_name"),
    }
    register_result = await api_request(page, base_api, "/auth/register", method="POST", body=register_payload)
    if not register_result.ok and register_result.status != 400:
        raise RuntimeError(f"Registration failed: {register_result.data}")

    await ensure_pow_cookie(page, base_api)

    login_payload = {"email": user["email"], "password": user["password"]}
    login_result = await api_request(page, base_api, "/auth/login", method="POST", body=login_payload)
    if not login_result.ok or not isinstance(login_result.data, dict):
        raise RuntimeError(f"Login failed: {login_result.data}")
    token = login_result.data.get("access_token")
    if not token:
        raise RuntimeError("Login response missing access token")

    products_result = await api_request(page, base_api, "/products", token=token)
    if not products_result.ok or not isinstance(products_result.data, list):
        raise RuntimeError(f"Could not list products: {products_result.data}")

    available = [p for p in products_result.data if isinstance(p, dict) and int(p.get("inventory_count", 0) or 0) > 0]
    if not available:
        raise RuntimeError("No available inventory to simulate")

    for _ in range(cart_actions):
        product = random.choice(available)
        max_qty = int(product.get("inventory_count", 1) or 1)
        quantity = random.randint(1, max(1, min(2, max_qty)))
        await ensure_pow_cookie(page, base_api, token=token)
        add_result = await api_request(
            page,
            base_api,
            "/cart/items",
            method="POST",
            token=token,
            body={"product_id": product["id"], "quantity": quantity},
        )
        if not add_result.ok:
            detail = add_result.data if isinstance(add_result.data, str) else add_result.data.get("detail")
            print(f"  Skipping {product.get('name')}: {detail}")
            refreshed = await api_request(page, base_api, "/products", token=token)
            if refreshed.ok and isinstance(refreshed.data, list):
                available = [p for p in refreshed.data if int(p.get("inventory_count", 0) or 0) > 0]
            if not available:
                break
            continue
        product["inventory_count"] = max(int(product.get("inventory_count", 0)) - quantity, 0)
        if int(product["inventory_count"]) <= 0:
            available = [p for p in available if p.get("id") != product["id"]]
            if not available:
                break

    cart_result = await api_request(page, base_api, "/cart", token=token)
    if not cart_result.ok or not isinstance(cart_result.data, dict):
        raise RuntimeError(f"Cart lookup failed: {cart_result.data}")
    items = cart_result.data.get("items", [])
    subtotal = cart_result.data.get("subtotal")
    print(f"Cart for {user['email']}: {len(items)} items, subtotal {subtotal}")

    await ensure_pow_cookie(page, base_api, token=token)
    order_result = await api_request(page, base_api, "/orders", method="POST", token=token, body={})
    if not order_result.ok or not isinstance(order_result.data, dict):
        raise RuntimeError(f"Checkout failed: {order_result.data}")
    print(f"Placed order {order_result.data.get('id')} with total {order_result.data.get('total_amount')}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Headless browser UAT for the API commerce demo")
    parser.add_argument("--base-url", default="http://localhost:8000/api", help="Base API URL (e.g., https://shop.example.com/api)")
    parser.add_argument("--iterations", type=int, default=1, help="Number of simulation loops to run")
    parser.add_argument("--users", type=int, default=3, help="Number of users to simulate (1-3)")
    parser.add_argument("--cart-actions", type=int, default=2, help="Number of add-to-cart actions per user")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between iterations in seconds")
    parser.add_argument("--headful", action="store_true", help="Run browser in headed mode for debugging")
    return parser.parse_args(list(argv))


async def main_async(args: argparse.Namespace) -> int:
    users = DEFAULT_USERS[: max(1, min(args.users, len(DEFAULT_USERS)))]
    parsed = urlparse(args.base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    base_api = args.base_url.rstrip("/")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headful)
        try:
            for iteration in range(1, args.iterations + 1):
                print(f"\nIteration {iteration}/{args.iterations}")
                for user in users:
                    context = await browser.new_context()
                    page = await context.new_page()
                    try:
                        await page.goto(origin, wait_until="domcontentloaded", timeout=60000)
                        await wait_for_edge_challenge(page, base_api)
                        await simulate_user(page, base_api, user, cart_actions=args.cart_actions)
                    except Exception as exc:  # logging only
                        print(f"User {user['email']} flow failed: {exc}")
                    finally:
                        await context.close()
                if iteration != args.iterations and args.delay > 0:
                    await asyncio.sleep(args.delay)
        finally:
            await browser.close()
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())

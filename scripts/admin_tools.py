"""Administrative helper script for the API-driven commerce demo."""

from __future__ import annotations

import argparse
import getpass
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional
from urllib.parse import urlparse, urlunparse

import requests


API_BASE_PATH = "/api/v1"


@dataclass
class AdminClient:
    base_url: str
    session: requests.Session
    token: Optional[str] = None

    def _url(self, path: str) -> str:
        base = self.base_url.rstrip("/")
        suffix = path if path.startswith("/") else f"/{path}"
        return f"{base}{suffix}"

    def request(self, method: str, path: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        response = self.session.request(method, self._url(path), headers=headers, timeout=15, **kwargs)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = None
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            if detail:
                raise RuntimeError(f"API request failed ({response.status_code}): {detail}") from exc
            raise
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def login(self, email: str, password: str) -> None:
        payload = {"email": email, "password": password}
        data = self.request("POST", "/auth/login", json=payload)
        self.token = data["access_token"]

    def reset_store(self) -> None:
        self.request("POST", "/admin/reset")

    def list_users(self):
        return self.request("GET", "/admin/users")

    def list_products(self):
        return self.request("GET", "/products")

    def update_product(
        self,
        product_id: int,
        *,
        price: Optional[Decimal] = None,
        inventory_count: Optional[int] = None,
    ):
        payload = {}
        if price is not None:
            payload["price"] = str(price)
        if inventory_count is not None:
            payload["inventory_count"] = inventory_count
        if not payload:
            raise ValueError("No updates provided for product.")
        return self.request("PUT", f"/products/{product_id}", json=payload)


def normalize_base_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path or path == "":
        path = API_BASE_PATH
    elif path == "/":
        path = API_BASE_PATH
    elif not path.startswith("/"):
        path = f"/{path}"
    if path == "/api":
        path = API_BASE_PATH
    normalized = parsed._replace(path=path)
    return urlunparse(normalized)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Administrative tools for the commerce API")
    parser.add_argument("--base-url", default=f"http://shop.exampledomain.com{API_BASE_PATH}", help="Base API URL")
    return parser.parse_args(list(argv))


def prompt_int(prompt: str) -> int:
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print("  Please enter a whole number.")


def prompt_optional_decimal(prompt: str) -> Optional[Decimal]:
    while True:
        value = input(prompt).strip()
        if value == "":
            return None
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            print("  Please enter a valid decimal number or leave blank to skip.")


def prompt_optional_int(prompt: str) -> Optional[int]:
    while True:
        value = input(prompt).strip()
        if value == "":
            return None
        try:
            return int(value)
        except ValueError:
            print("  Please enter a whole number or leave blank to skip.")


def choose_menu_option() -> str:
    print("\nAvailable actions:")
    print("  1) Reset Store Data")
    print("  2) View Product Inventory")
    print("  3) Update Product Inventory & Price")
    print("  4) View Registered Users")
    print("  5) Exit")
    return input("Select an option: ").strip()


def handle_reset(client: AdminClient) -> None:
    confirm = input("This will reset all store data. Type 'RESET' to confirm: ").strip()
    if confirm != "RESET":
        print("  Reset cancelled.")
        return
    client.reset_store()
    print("  Store reset complete.")


def handle_update_product(client: AdminClient) -> None:
    products = client.list_products()
    if not products:
        print("  No products available to update.")
        return
    print("\nCurrent products:")
    for product in products:
        print(
            f"  ID {product['id']}: {product['name']} (Inventory: {product['inventory_count']}, Price: {product['price']})"
        )
    product_lookup = {int(prod["id"]): prod for prod in products}
    product_id = prompt_int("Enter product ID to update: ")
    product = product_lookup.get(product_id)
    if not product:
        print("  Product not found.")
        return
    current_inventory = product.get("inventory_count")
    current_price = product.get("price")
    inventory = prompt_optional_int(
        f"Enter new total inventory count (current {current_inventory}, leave blank to keep): "
    )
    price = prompt_optional_decimal(
        f"Enter new price (current {current_price}, leave blank to keep): "
    )
    if inventory is None and price is None:
        print("  No changes provided; skipping update.")
        return
    client.update_product(product_id, price=price, inventory_count=inventory)
    print("  Product updated successfully.")


def handle_view_users(client: AdminClient) -> None:
    users = client.list_users()
    if not users:
        print("  No registered users found.")
        return
    print("\nRegistered users:")
    for user in users:
        flag = "(admin)" if user.get("is_admin") else ""
        print(f"  {user['id']}: {user['email']} {flag}")


def handle_view_inventory(client: AdminClient) -> None:
    products = client.list_products()
    if not products:
        print("  No products available.")
        return
    print("\nCurrent inventory:")
    for product in products:
        print(
            f"  ID {product['id']}: {product['name']} (Inventory: {product['inventory_count']}, Price: {product['price']})"
        )


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    base_url = normalize_base_url(args.base_url)
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password: ")
    session = requests.Session()
    client = AdminClient(base_url=base_url, session=session)
    try:
        client.login(email, password)
        print("Login successful.")
        while True:
            choice = choose_menu_option()
            if choice == "1":
                handle_reset(client)
            elif choice == "2":
                handle_view_inventory(client)
            elif choice == "3":
                handle_update_product(client)
            elif choice == "4":
                handle_view_users(client)
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("  Invalid selection. Please choose 1-5.")
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

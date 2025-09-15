from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    exp: int


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    is_admin: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    name: str
    description: str
    price: Decimal = Field(gt=0)
    inventory_count: int = Field(ge=0)
    image_url: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    price: Optional[Decimal]
    inventory_count: Optional[int]
    image_url: Optional[str]
    is_active: Optional[bool]


class ProductRead(ProductBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class CartItemRead(BaseModel):
    id: int
    product: ProductRead
    quantity: int
    added_at: datetime

    class Config:
        orm_mode = True


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartSummary(BaseModel):
    items: List[CartItemRead]
    subtotal: Decimal

    class Config:
        orm_mode = True


class OrderItemRead(BaseModel):
    id: int
    product: ProductRead
    quantity: int
    unit_price: Decimal

    class Config:
        orm_mode = True


class OrderCreate(BaseModel):
    shipping_address: Optional[str] = None


class OrderRead(BaseModel):
    id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    items: List[OrderItemRead]

    class Config:
        orm_mode = True

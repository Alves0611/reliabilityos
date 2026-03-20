import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str]
    price: Decimal
    stock: int
    created_at: datetime


class OrderItemRequest(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    items: List[OrderItemRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    total: Decimal
    created_at: datetime
    updated_at: datetime


class OrderDetailResponse(OrderResponse):
    items: List[OrderItemResponse]


class HealthResponse(BaseModel):
    status: str
    database: str
    rabbitmq: str

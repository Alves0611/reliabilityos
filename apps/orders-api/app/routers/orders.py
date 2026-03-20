import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import messaging
from app.database import get_db
from app.metrics import ORDERS_TOTAL, PRODUCT_STOCK
from app.models import Order, OrderItem, Product
from app.schemas import (
    CreateOrderRequest,
    OrderDetailResponse,
    OrderResponse,
)
from app.telemetry import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer()

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: CreateOrderRequest, db: AsyncSession = Depends(get_db)
):
    with tracer.start_as_current_span("create_order") as span:
        order_items = []
        total = Decimal("0")

        for item in payload.items:
            result = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = result.scalar_one_or_none()
            if product is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product {item.product_id} not found",
                )
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock}, requested: {item.quantity}",
                )

            product.stock -= item.quantity
            line_total = product.price * item.quantity
            total += line_total

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=product.price,
                )
            )

            PRODUCT_STOCK.labels(product_name=product.name).set(product.stock)

        order = Order(total=total, items=order_items)
        db.add(order)
        await db.commit()
        await db.refresh(order, attribute_names=["items"])

        span.set_attribute("order.id", str(order.id))
        span.set_attribute("order.total", float(total))
        span.set_attribute("order.items_count", len(order_items))

        ORDERS_TOTAL.labels(status="pending").inc()
        logger.info("Order created", extra={"order_id": str(order.id), "total": float(total)})

        await messaging.publish_task(
            task_name="worker.tasks.process_order",
            args=[str(order.id)],
            routing_key="order.created",
        )

        return order


@router.get("", response_model=list[OrderResponse])
async def list_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.refresh(order, attribute_names=["items"])
    return order

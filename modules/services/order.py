from decimal import Decimal
from typing import Any
from sqlalchemy.orm import Session
from ..database.models import OrderDB
from ..repositories.order import OrderRepository
from ..repositories.user import UserRepository
from ..repositories.product import ProductRepository
from ..schemas import OrderItem, OrderResponse, OrderItemResponse


class OrderService:

    def __init__(
        self,
        session: Session,
    ):
        self.session = session
        self.order_repository = OrderRepository(session)
        self.user_repository = UserRepository(session)
        self.product_repository = ProductRepository(session)
        

    def create_order(
        self,
        *,
        user_id: str,
        items: list[OrderItem],
        address: str,
        status: str,
    ) -> OrderDB:
        try:

            order_items, total = self.calculate_order(items)

            serialized_items = self._serialize_order_items(order_items)

            order = self.order_repository.create(
                user_id=int(user_id),
                items=serialized_items,
                address=address,
                total=total,
                status=status,
            )
  
            self.user_repository.update_last_orders(
                user_id=int(user_id),
                last_order={
                    "order_id": order.id,
                    "items": serialized_items,        
                    "address": address,
                    "total": str(total),
                    "status": status,
                },
            )

            self.user_repository.update_last_order_id(
                user_id = int(user_id),
                order_id = order.id,
            )

            self.user_repository.update_address(
                user_id = int(user_id),
                address = address
            )

            self.session.commit()
            return order

        except Exception:
            self.session.rollback()
            raise


    def calculate_order(
        self,
        items: list[OrderItem],
    ) -> tuple[list[dict], Decimal]:

        if not items:
            raise ValueError("Заказ не может быть пустым")

        order_items = []
        total = Decimal("0")

        for item in items:
            product = self.product_repository.get_by_name(item.name)

            if product is None:
                raise ValueError(
                    f"Пицца '{item.name}' не найдена"
                )

            item_total = (
                product.price * item.quantity
            )

            order_items.append({
                "name": product.name,
                "price": product.price,
                "quantity": item.quantity,
                "subtotal": item_total,
            })

            total += item_total

        return order_items, total

    @staticmethod
    def _to_schema(order: OrderDB) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            items=[
                OrderItemResponse(
                    name=item["name"],
                    price=Decimal(item["price"]),
                    quantity=item["quantity"],
                    subtotal=Decimal(item["subtotal"]),
                )
                for item in order.items
            ],
            address=order.address,
            total=order.total,
            status=order.status,
            created_at=order.created_at,
        )

    @staticmethod
    def _serialize_order_items(
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        return [
            {
                **item,
                "price": str(item["price"]),
                "subtotal": str(item["subtotal"]),
            }
            for item in items
        ]   
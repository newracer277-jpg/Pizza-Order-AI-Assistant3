from dataclasses import dataclass
from typing import Any


@dataclass
class PendingOrder:
    config: dict[str, Any]
    order: dict[str, Any]


_pending_orders: dict[int, PendingOrder] = {}


def set_pending_order(
    user_id: int,
    config: dict[str, Any],
    order: dict[str, Any],
) -> None:

    _pending_orders[user_id] = PendingOrder(
        config=config,
        order=order,
    )


def get_pending_order(
    user_id: int,
) -> PendingOrder | None:

    return _pending_orders.get(user_id)


def delete_pending_order(
    user_id: int,
) -> None:

    _pending_orders.pop(user_id, None)
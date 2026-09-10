from langgraph.types import Command
from langchain.agents.middleware import HumanInTheLoopMiddleware
from ..database import SessionLocal
from ..repositories.product import ProductRepository

class HITLManager:
    def __init__(self, agent, config):
        self.agent = agent
        self.config = config

    def invoke(self, message):

        state = self.agent.get_state(self.config)

        if state.values.get("__interrupt__"):
            decision = {
                "type": "reject",
                "message": f"Пользователь изменил ввод на: {message}",
            }

            self.agent.invoke(
                Command(
                    resume={
                        "decisions": [decision]
                    }
                ),
                config=self.config,
            )

        response = self.agent.invoke(
            {"messages": [message]},
            config=self.config,
        )

        while response.get("__interrupt__"):
            response = self.resolve(response)

        return response


    def resolve(self, response):
        interrupt_data = response["__interrupt__"]

        if isinstance(interrupt_data, (tuple, list)) and interrupt_data:
            interrupt_data = interrupt_data[0]

        action = interrupt_data.value["action_requests"][0]

        print("\n=== Требуется подтверждение ===")
        print("Заказ:")

        order = action.get("args", {})
        items = order.get("items", [])

        for item in items:
            name = item.get("name", "")
            quantity = item.get("quantity", "")
            price = item.get("price", "")
            subtotal = item.get("subtotal", "")

            print(
                f"Пицца: {name} — "
                f"{quantity} шт. × {price} руб. = {subtotal} руб."
            )

        total = order.get("total", "")
        address = order.get("address", "")

        print(f"\nОбщая стоимость: {total} руб.")
        print(f"Адрес доставки: {address}")

        answer = input(
            "\nПодтвердить заказ? [да/нет]: "
        ).strip().lower()

        if answer in ("да", "д", "y", "yes"):
            decision = {
                "type": "approve"
            }

        else:
            decision = {
                "type": "reject",
                "message": (
                    "Заказ отклонён пользователем. "
                    "Не сохраняй этот заказ и не используй "
                    "его данные для следующего заказа. "
                    "Если пользователь продолжит диалог, "
                    "начни оформление нового заказа заново. "
                    "Цены всегда бери только из базы данных."
                ),
            }

        return self.agent.invoke(
            Command(
                resume={
                    "decisions": [decision]
                }
            ),
            config=self.config,
        )


hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "save_order": True
    }
)

from langgraph.types import Command
from langchain.agents.middleware import HumanInTheLoopMiddleware


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
                Command(resume={"decisions": [decision]}),
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

        if isinstance(interrupt_data, (tuple, list)):
            interrupt_data = interrupt_data[0]

        action = interrupt_data.value["action_requests"][0]
        order = action.get("args", {})

        print("\n=== Требуется подтверждение ===")
        print("Заказ:")

        items = order.get("items", [])

        for item in items:
            name = item.get("name", "Неизвестная пицца")
            quantity = item.get("quantity", 0)
            price = item.get("price", "0")
            subtotal = item.get("subtotal", "0")

            print(
                f"Пицца: {name} — "
                f"{quantity} шт. × {price} руб. = "
                f"{subtotal} руб."
            )

        total = order.get("total", "0")
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
                "message": "Заказ отклонён пользователем",
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

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
                "message": (
                    "Пользователь изменил ввод. "
                    "Предыдущий заказ отменён."
                ),
            }

            self.agent.invoke(
                Command(
                    resume={
                        "decisions": [decision]
                    }
                ),
                config=self.config,
            )

        return self.agent.invoke(
            {"messages": [message]},
            config=self.config,
        )

    def resume(self, decision):

        return self.agent.invoke(
            Command(
                resume={
                    "decisions": [decision]
                }
            ),
            config=self.config,
        )

    @staticmethod
    def get_order_from_interrupt(response):

        interrupt_data = response.get("__interrupt__")

        if not interrupt_data:
            return None

        if isinstance(interrupt_data, (tuple, list)):
            interrupt_data = interrupt_data[0]

        return interrupt_data.value["action_requests"][0]


hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "save_order": True
    }
)
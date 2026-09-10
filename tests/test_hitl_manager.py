from langchain.messages import HumanMessage
from langgraph.types import Command

from modules.middleware.order_confirmation import HITLManager


class FakeAgent:

    def __init__(self, responses=None):
        self.responses = responses or []
        self.calls = []

    def get_state(self, config):
        return FakeState()

    def invoke(self, payload, config=None):
        self.calls.append(payload)

        if self.responses:
            return self.responses.pop(0)

        return {
            "messages": [
                HumanMessage(content="Заказ сохранён")
            ]
        }


class FakeState:

    def __init__(self, values=None):
        self.values = values or {}


def make_interrupt(
    items=None,
    total="678",
    address="Победа 22",
):
    class FakeInterrupt:

        def __init__(self):
            self.value = {
                "action_requests": [
                    {
                        "name": "save_order",
                        "args": {
                            "items": items or [
                                {
                                    "name": "Маргарита",
                                    "quantity": 2,
                                    "price": "339",
                                    "subtotal": "678",
                                }
                            ],
                            "total": total,
                            "address": address,
                        },
                    }
                ]
            }

    return FakeInterrupt()


def test_hitl_approve_order(monkeypatch):
    interrupt = make_interrupt()

    agent = FakeAgent(
        responses=[
            {
                "__interrupt__": [interrupt]
            },
            {
                "messages": [
                    HumanMessage(
                        content="Заказ успешно сохранён"
                    )
                ]
            },
        ]
    )

    manager = HITLManager(
        agent=agent,
        config={"configurable": {"thread_id": "test"}},
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "да",
    )

    response = manager.invoke(
        HumanMessage(
            content="хочу Маргариту"
        )
    )

    last_call = agent.calls[-1]

    assert isinstance(last_call, Command)

    assert last_call.resume["decisions"][0] == {
        "type": "approve"
    }

    assert (
        response["messages"][-1].content
        == "Заказ успешно сохранён"
    )


def test_hitl_reject_order(monkeypatch):
    interrupt = make_interrupt()

    agent = FakeAgent(
        responses=[
            {
                "__interrupt__": [interrupt]
            },
            {
                "messages": [
                    HumanMessage(
                        content="Заказ отклонён пользователем"
                    )
                ]
            },
        ]
    )

    manager = HITLManager(
        agent=agent,
        config={"configurable": {"thread_id": "test"}},
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "нет",
    )

    response = manager.invoke(
        HumanMessage(
            content="хочу Маргариту"
        )
    )

    last_call = agent.calls[-1]

    assert isinstance(last_call, Command)

    decision = last_call.resume["decisions"][0]

    assert decision["type"] == "reject"
    assert decision["message"].startswith(
        "Заказ отклонён пользователем"
    )

    assert (
        response["messages"][-1].content
        == "Заказ отклонён пользователем"
    )


def test_hitl_accepts_short_yes(monkeypatch):
    interrupt = make_interrupt()

    agent = FakeAgent(
        responses=[
            {
                "__interrupt__": [interrupt]
            },
            {
                "messages": [
                    HumanMessage(content="Заказ сохранён")
                ]
            },
        ]
    )

    manager = HITLManager(
        agent=agent,
        config={},
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "д",
    )

    manager.invoke(
        HumanMessage(content="оформить")
    )

    decision = agent.calls[-1].resume["decisions"][0]

    assert decision["type"] == "approve"


def test_hitl_any_other_answer_rejects(monkeypatch):
    interrupt = make_interrupt()

    agent = FakeAgent(
        responses=[
            {
                "__interrupt__": [interrupt]
            },
            {
                "messages": [
                    HumanMessage(content="Отклонено")
                ]
            },
        ]
    )

    manager = HITLManager(
        agent=agent,
        config={},
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "что-то другое",
    )

    manager.invoke(
        HumanMessage(content="оформить")
    )

    decision = agent.calls[-1].resume["decisions"][0]

    assert decision["type"] == "reject"


def test_hitl_rejects_previous_interrupt_when_new_message_arrives():
    class AgentWithPendingInterrupt(FakeAgent):

        def get_state(self, config):
            return FakeState(
                values={
                    "__interrupt__": True
                }
            )

    agent = AgentWithPendingInterrupt(
        responses=[
            {
                "messages": [
                    HumanMessage(content="Новое сообщение")
                ]
            }
        ]
    )

    manager = HITLManager(
        agent=agent,
        config={},
    )

    manager.invoke(
        HumanMessage(
            content="я хочу другую пиццу"
        )
    )

    first_call = agent.calls[0]

    assert isinstance(first_call, Command)

    decision = first_call.resume["decisions"][0]

    assert decision["type"] == "reject"

    assert (
        decision["message"]
        == "Пользователь изменил ввод на: "
        "content='я хочу другую пиццу' additional_kwargs={} "
        "response_metadata={}"
    )    
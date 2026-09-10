from typing import Any
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from telegram.hitl import get_pending_order
from . import tools
from .model import model
from .system_prompt import system_prompt
from .middleware import HITLManager, hitl
from .database import (
    AgentPersistence,
    SessionLocal,
)
from .services import UserService
from .context import current_user_id


persistence = AgentPersistence()


agent: Any = create_agent(
    model,
    tools=tools.AGENT_TOOLS,
    checkpointer=persistence.checkpointer,
    store=persistence.store,
    system_prompt=system_prompt,
    middleware=(
        hitl,
    ),
)


def get_agent_response(
    message: str,
    user_id: int,
):
    """
    Обработка сообщения пользователя
    и запуск AI-агента.
    """

    token = current_user_id.set(user_id)

    try:

        thread_id = f"user:{user_id}"

        runtime_config = {
            "configurable": {
                "user_id": user_id,
                "thread_id": thread_id,
            }
        }

        with SessionLocal() as session:

            service = UserService(
                session=session,
                store=persistence.store,
            )

            service.load_user_to_store(user_id)

            hitl_manager = HITLManager(
                agent=agent,
                config=runtime_config,
            )

            response = hitl_manager.invoke(
                HumanMessage(
                    content=message
                )
            )

        return response

    finally:

        current_user_id.reset(token)


def resume_agent(
    user_id: int,
    decision: dict,
):
    """
    Продолжает выполнение агента
    после решения пользователя в HITL.
    """

    token = current_user_id.set(user_id)

    try:

        pending = get_pending_order(user_id)

        if pending is None:
            raise ValueError(
                "Ожидающее подтверждение заказа не найдено."
            )

        hitl_manager = HITLManager(
            agent=agent,
            config=pending.config,
        )

        response = hitl_manager.resume(
            decision
        )

        return response

    finally:

        current_user_id.reset(token)


def run_cycle():

    while True:

        question_text = input(">>> ")

        if not question_text:
            break

        response = get_agent_response(
            message=question_text,
            user_id=1,
        )

        if response.get("__interrupt__"):
            print(
                "Требуется подтверждение заказа."
            )
            continue

        print(
            response["messages"][-1].content
        )
from typing import Any
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from . import tools
from .model import model
from .system_prompt import system_prompt
from .middleware import HITLManager, hitl, history_trimmer
from .database import AgentPersistence
from .config import config
from .database import SessionLocal
from .services import UserService


persistence = AgentPersistence()


user_id = config.get("configurable", {}).get("user_id")



with SessionLocal() as session:
    service = UserService(
        session=session,
        store=persistence.store,
    )

    

agent: Any = create_agent(
    model,
    tools=tools.AGENT_TOOLS,
    checkpointer=persistence.checkpointer,
    store=persistence.store,
    system_prompt=system_prompt,
    middleware=(
        # history_trimmer,
        hitl,
    ),
)


hitl_manager = HITLManager(
    agent=agent,
    config=config,
)


def run_cycle():
    while True:
        question_text = input(">>> ")

        if not question_text:
            break

        response = hitl_manager.invoke(
            HumanMessage(content=question_text)
        )

        if user_id is None:
           return print("user_id не указан в config")

        service.load_user_to_store(user_id)

        print(response["messages"][-1].content)
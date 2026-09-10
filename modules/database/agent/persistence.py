import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.sqlite import SqliteStore


class AgentPersistence:

    def __init__(
        self,
        checkpoint_db: str = "database/agent.db",
        store_db: str = "database/agent.db",
    ):
        self.checkpoint_conn = sqlite3.connect(
            checkpoint_db,
            check_same_thread=False,
            isolation_level=None,
        )

        self.store_conn = sqlite3.connect(
            store_db,
            check_same_thread=False,
            isolation_level=None,
        )

        self.checkpointer = SqliteSaver(
            self.checkpoint_conn
        )

        self.store = SqliteStore(
            self.store_conn
        )

        self.store.setup()

    def close(self) -> None:
        self.checkpoint_conn.close()
        self.store_conn.close()
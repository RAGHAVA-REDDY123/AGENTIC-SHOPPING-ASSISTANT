import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

root_env = Path(__file__).resolve().parents[2] / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, class_=Session)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_connection() -> dict:
    """Test database connectivity and check if pgvector extension is installed."""
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version();")).scalar()
            has_vector = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');")
            ).scalar()
            return {
                "status": "connected",
                "database": engine.url.render_as_string(hide_password=True),
                "postgres_version": version,
                "pgvector_installed": bool(has_vector),
            }
    except Exception as exc:
        return {
            "status": "failed",
            "database": engine.url.render_as_string(hide_password=True),
            "error": str(exc),
            "pgvector_installed": False,
        }


if __name__ == "__main__":
    result = check_db_connection()
    print("Database Connection Status:", result)

    if result.get("status") != "connected":
        print("Database is not connected. Please ensure Docker is running.")
        raise SystemExit(1)

    import sys
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from backend.graph.workflow import shopping_workflow
    from langchain_core.messages import HumanMessage

    thread_id = "interactive_session_001"
    agent_config = {"configurable": {"thread_id": thread_id}}

    print("\n=== AI Shopping Assistant ===")
    print("Type your query or 'exit' to quit.\n")

    ans = {}
    while True:
        try:
            user_query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not user_query or user_query.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        try:
            prior_len = len(ans.get("messages", []))
            ans = shopping_workflow.invoke(
                {"messages": [HumanMessage(content=user_query)]},
                config=agent_config,
            )
            messages = ans.get("messages", [])
            new_ai_msgs = [
                m.content for m in messages[prior_len:]
                if getattr(m, "type", "") == "ai" and m.content
            ]
            reply = "\n\n".join(new_ai_msgs) if new_ai_msgs else (messages[-1].content if messages else "Done.")
            print(f"\nAssistant:\n{reply}\n")
        except Exception as err:
            print(f"\n[Error]: {err}\n")

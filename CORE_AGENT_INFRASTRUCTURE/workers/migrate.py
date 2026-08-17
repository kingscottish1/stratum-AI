"""DB migrations entrypoint (idempotent create_all + future Alembic hooks)."""
from CORE_AGENT_INFRASTRUCTURE.config import resolve_config
from CORE_AGENT_INFRASTRUCTURE.db.session import init_db


def main() -> None:
    resolve_config()
    init_db()
    print("migrations applied")


if __name__ == "__main__":
    main()

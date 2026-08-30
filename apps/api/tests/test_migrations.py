import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_is_repeatable(tmp_path: Path) -> None:
    api_dir = Path(__file__).resolve().parents[1]
    database = tmp_path / "migration.db"
    env = {**os.environ, "OPSASSIST_DATABASE_URL": f"sqlite:///{database}", "PYTHONPATH": str(api_dir)}
    command = [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"]
    subprocess.run(command, cwd=api_dir, env=env, check=True)
    subprocess.run(command, cwd=api_dir, env=env, check=True)
    columns = {item["name"] for item in inspect(create_engine(f"sqlite:///{database}")).get_columns("incidents")}
    assert "tenant_id" in columns

from __future__ import annotations

import json

from _bootstrap import ROOT  # noqa: F401
from app.core.config import get_settings
from app.db.base import SessionLocal, create_schema
from app.db.models import Service
from app.services.scenarios import ScenarioLoader


def main() -> None:
    create_schema()
    loader = ScenarioLoader(ROOT / "data" / "scenarios")
    service_ids: set[str] = set()
    for scenario_id in loader.list():
        service_ids.update(loader.load(scenario_id)["topology"]["nodes"])
    with SessionLocal() as session:
        for service_id in sorted(service_ids):
            session.merge(Service(id=service_id, name=service_id.replace("_", " ").title(), synthetic=True))
        session.commit()
    print(json.dumps({"seeded_services": len(service_ids), "scenarios": loader.list(), "synthetic": True}, indent=2))


if __name__ == "__main__":
    main()

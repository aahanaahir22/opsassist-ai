import json

from app.schemas.models import KnowledgeDocumentIn
from app.services.retrieval import RetrievalService


def test_index_promotion_is_versioned_and_atomic(tmp_path) -> None:
    service = RetrievalService(tmp_path)
    document = KnowledgeDocumentIn(
        document_id="RB-TEST", version="1.0", title="Test", content="database pool timeout rollback procedure",
        service_ids=["checkout"], document_type="runbook", trust_level="verified",
    )
    assert service.build([document], persist=True) == 1
    pointer = json.loads((tmp_path / "current.json").read_text())
    active = tmp_path / "versions" / pointer["version"]
    assert active.joinpath("manifest.json").exists()
    assert not list(tmp_path.rglob("*.staging"))

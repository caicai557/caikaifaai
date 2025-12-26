import pytest

from council.memory.knowledge_graph import (
    EntityType,
    KnowledgeGraph,
    RelationType,
)


def test_json_persistence_round_trip(tmp_path):
    storage = tmp_path / "kg.json"
    kg = KnowledgeGraph(storage_path=storage, auto_load=False)

    kg.add_entity("file_1", EntityType.FILE, "auth.py", {"path": "src/auth.py"})
    kg.add_entity("decision_1", EntityType.DECISION, "使用JWT认证")
    kg.add_relation(
        "decision_1",
        "file_1",
        RelationType.IMPLEMENTS,
        {"notes": "initial version"},
        weight=0.8,
    )

    assert kg.save()
    assert storage.exists()

    loaded = KnowledgeGraph(storage_path=storage, auto_load=True)

    entity = loaded.get_entity("file_1")
    assert entity is not None
    assert entity.properties["path"] == "src/auth.py"

    related = loaded.get_related("decision_1", RelationType.IMPLEMENTS)
    assert len(related) == 1
    assert related[0][0].id == "file_1"
    assert related[0][1].weight == pytest.approx(0.8)


def test_gml_persistence_round_trip(tmp_path):
    pytest.importorskip("networkx")

    storage = tmp_path / "kg.gml"
    kg = KnowledgeGraph(storage_path=storage, auto_load=False)

    kg.add_entity("task_1", EntityType.TASK, "需求分析", {"priority": "high"})
    kg.add_entity("agent_coder", EntityType.AGENT, "Coder")
    kg.add_relation(
        "task_1",
        "agent_coder",
        RelationType.RELATED_TO,
        {"role": "owner"},
        weight=0.6,
    )

    assert kg.save()
    assert storage.exists()

    loaded = KnowledgeGraph(storage_path=storage, auto_load=True)

    task = loaded.get_entity("task_1")
    assert task is not None
    assert task.properties["priority"] == "high"

    related = loaded.get_related("task_1")
    assert any(rel.relation_type == RelationType.RELATED_TO for _, rel in related)
    assert related[0][1].weight == pytest.approx(0.6)

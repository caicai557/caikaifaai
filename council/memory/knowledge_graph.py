"""
Knowledge Graph - 知识图谱接口
为智能体提供结构化的长期记忆和语义关系查询
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from copy import deepcopy

try:
    import networkx as nx
except ImportError:  # pragma: no cover - optional dependency
    nx = None


DEFAULT_STORAGE_PATH = Path(".council/knowledge_graph.gml")


class RelationType(Enum):
    """关系类型"""

    DEPENDS_ON = "depends_on"  # A 依赖 B
    IMPLEMENTS = "implements"  # A 实现 B
    CONTAINS = "contains"  # A 包含 B
    RELATED_TO = "related_to"  # A 与 B 相关
    DECIDED_BY = "decided_by"  # A 由 B 决定
    APPROVED_BY = "approved_by"  # A 被 B 批准
    CREATED_BY = "created_by"  # A 由 B 创建
    SUPERSEDES = "supersedes"  # A 取代 B
    IMPORTS = "imports"  # A 导入 B (代码依赖)


class EntityType(Enum):
    """实体类型"""

    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    DECISION = "decision"
    AGENT = "agent"
    TASK = "task"
    PROPOSAL = "proposal"
    POLICY = "policy"


@dataclass
class Entity:
    """知识图谱实体"""

    id: str
    entity_type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.entity_type.value,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Relation:
    """知识图谱关系"""

    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type.value,
            "properties": self.properties,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
        }


class KnowledgeGraph:
    """
    轻量级知识图谱实现

    核心功能:
    1. 存储实体和关系
    2. 支持语义查询
    3. 持久化到文件 (.gml 或 .json)

    可扩展为连接 Neo4j / FalkorDB

    使用示例:
        kg = KnowledgeGraph()  # 默认使用 .council/knowledge_graph.gml

        # 添加实体
        kg.add_entity("file_1", EntityType.FILE, "auth.py", {"path": "src/auth.py"})
        kg.add_entity("decision_1", EntityType.DECISION, "使用JWT认证")

        # 添加关系
        kg.add_relation("decision_1", "file_1", RelationType.IMPLEMENTS)

        # 查询
        related = kg.get_related("file_1", RelationType.IMPLEMENTS)
    """

    def __init__(self, storage_path: Optional[str] = None, auto_load: bool = True):
        """
        初始化知识图谱

        Args:
            storage_path: 持久化路径，默认 .council/knowledge_graph.gml
            auto_load: 是否在初始化时自动加载已有文件
        """
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.storage_path = (
            Path(storage_path) if storage_path is not None else DEFAULT_STORAGE_PATH
        )

        # 索引
        self._entity_by_type: Dict[EntityType, Set[str]] = {}
        self._relations_from: Dict[str, List[Relation]] = {}
        self._relations_to: Dict[str, List[Relation]] = {}

        # Hybrid Search: Initialize Vector Store BEFORE auto_load
        try:
            from council.memory.vector_memory import VectorMemory

            # Use VectorMemory (unified vector storage)
            self.vector_store = VectorMemory(
                persist_dir=str(self.storage_path.parent / "vectors"),
                collection_name="knowledge_graph",
            )
        except ImportError:
            self.vector_store = None

        if auto_load:
            self.load()

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        """解析日期字符串，失败时返回当前时间"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now()

    @staticmethod
    def _serialize_properties(properties: Dict[str, Any]) -> str:
        """将属性序列化为 JSON 字符串，确保 GML 兼容"""
        try:
            return json.dumps(properties, ensure_ascii=False)
        except TypeError:
            safe_props = {k: str(v) for k, v in properties.items()}
            return json.dumps(safe_props, ensure_ascii=False)

    @staticmethod
    def _require_networkx() -> None:
        if nx is None:
            raise ImportError(
                "networkx 未安装，无法使用 GML 持久化。请安装 networkx>=3.2.0"
            )

    @property
    def storage_format(self) -> str:
        """返回持久化格式 (gml/json/unknown)"""
        if not self.storage_path:
            return "none"
        suffix = self.storage_path.suffix.lower()
        if suffix == ".gml":
            return "gml"
        if suffix == ".json":
            return "json"
        return "unknown"

    def _sync_to_vector_store(self, entity: Entity):
        """Sync entity to vector store for semantic search."""
        if self.vector_store:
            # Create a rich text representation
            text = f"{entity.entity_type.value}: {entity.name}\\nProperties: {json.dumps(entity.properties, ensure_ascii=False)}"
            # Use VectorMemory.add() API
            self.vector_store.add(
                text=text,
                metadata={"type": entity.entity_type.value, "name": entity.name},
                doc_id=entity.id,
            )

    def add_entity(
        self,
        entity_id: str,
        entity_type: EntityType,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> Entity:
        """
        添加实体
        """
        entity = Entity(
            id=entity_id,
            entity_type=entity_type,
            name=name,
            properties=properties or {},
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
        )
        self.entities[entity_id] = entity

        # 更新索引
        if entity_type not in self._entity_by_type:
            self._entity_by_type[entity_type] = set()
        self._entity_by_type[entity_type].add(entity_id)

        # Sync to Vector Store
        self._sync_to_vector_store(entity)

        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """获取实体"""
        return self.entities.get(entity_id)

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
        created_at: Optional[datetime] = None,
    ) -> Optional[Relation]:
        """
        添加关系

        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 属性
            weight: 权重
            created_at: 创建时间（用于持久化恢复）

        Returns:
            创建的关系，如果实体不存在则返回None
        """
        if source_id not in self.entities or target_id not in self.entities:
            return None

        relation = Relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
            weight=weight,
            created_at=created_at or datetime.now(),
        )
        self.relations.append(relation)

        # 更新索引
        if source_id not in self._relations_from:
            self._relations_from[source_id] = []
        self._relations_from[source_id].append(relation)

        if target_id not in self._relations_to:
            self._relations_to[target_id] = []
        self._relations_to[target_id].append(relation)

        return relation

    def get_related(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both",  # "from" | "to" | "both"
    ) -> List[Tuple[Entity, Relation]]:
        """
        获取相关实体

        Args:
            entity_id: 实体ID
            relation_type: 可选的关系类型过滤
            direction: 方向

        Returns:
            (实体, 关系) 元组列表
        """
        results = []

        if direction in ["from", "both"]:
            for rel in self._relations_from.get(entity_id, []):
                if relation_type is None or rel.relation_type == relation_type:
                    target = self.entities.get(rel.target_id)
                    if target:
                        results.append((target, rel))

        if direction in ["to", "both"]:
            for rel in self._relations_to.get(entity_id, []):
                if relation_type is None or rel.relation_type == relation_type:
                    source = self.entities.get(rel.source_id)
                    if source:
                        results.append((source, rel))

        return results

    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """按类型获取实体"""
        ids = self._entity_by_type.get(entity_type, set())
        return [self.entities[i] for i in ids if i in self.entities]

    def query(
        self,
        entity_type: Optional[EntityType] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> List[Entity]:
        """
        查询实体

        Args:
            entity_type: 可选的类型过滤
            properties: 可选的属性过滤

        Returns:
            匹配的实体列表
        """
        results = []

        candidates = (
            self.get_entities_by_type(entity_type)
            if entity_type
            else list(self.entities.values())
        )

        for entity in candidates:
            if properties:
                match = all(
                    entity.properties.get(k) == v for k, v in properties.items()
                )
                if match:
                    results.append(entity)
            else:
                results.append(entity)

        return results

    def search_hybrid(self, query_text: str, limit: int = 5) -> List[Entity]:
        """
        混合搜索: 语义搜索 + 图谱实体
        """
        results = []
        if self.vector_store:
            # Semantic search using VectorMemory API
            search_res = self.vector_store.search(query_text, k=limit)
            # VectorMemory returns list of dicts with 'id' key
            for item in search_res:
                eid = item.get("id")
                if eid and eid in self.entities:
                    results.append(self.entities[eid])
        return results

    def record_decision(
        self,
        decision_id: str,
        description: str,
        agents: List[str],
        related_entities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Entity:
        """
        记录决策 - 便捷方法

        Args:
            decision_id: 决策ID
            description: 决策描述
            agents: 参与的智能体
            related_entities: 相关实体ID列表
            metadata: 附加元数据

        Returns:
            决策实体
        """
        decision = self.add_entity(
            entity_id=decision_id,
            entity_type=EntityType.DECISION,
            name=description,
            properties={
                "agents": agents,
                "metadata": metadata or {},
            },
        )

        # 添加关系
        for agent_name in agents:
            agent_id = f"agent_{agent_name.lower()}"
            if agent_id not in self.entities:
                self.add_entity(agent_id, EntityType.AGENT, agent_name)
            self.add_relation(decision_id, agent_id, RelationType.DECIDED_BY)

        for entity_id in related_entities:
            if entity_id in self.entities:
                self.add_relation(decision_id, entity_id, RelationType.RELATED_TO)

        return decision

    def _reset(self) -> None:
        """清空现有数据"""
        self.entities.clear()
        self.relations.clear()
        self._entity_by_type.clear()
        self._relations_from.clear()
        self._relations_to.clear()

    def _save_json(self) -> None:
        data = {
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations],
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_gml(self) -> None:
        self._require_networkx()
        graph = nx.MultiDiGraph()

        for entity in self.entities.values():
            graph.add_node(
                entity.id,
                type=entity.entity_type.value,
                name=entity.name,
                properties=self._serialize_properties(deepcopy(entity.properties)),
                created_at=entity.created_at.isoformat(),
                updated_at=entity.updated_at.isoformat(),
            )

        for rel in self.relations:
            graph.add_edge(
                rel.source_id,
                rel.target_id,
                type=rel.relation_type.value,
                properties=self._serialize_properties(deepcopy(rel.properties)),
                weight=rel.weight,
                created_at=rel.created_at.isoformat(),
            )

        nx.write_gml(graph, self.storage_path)

    def save(self) -> bool:
        """保存到文件"""
        if not self.storage_path:
            return False

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            if self.storage_format == "gml":
                self._save_gml()
            else:
                self._save_json()
            return True
        except Exception as e:
            print(f"保存知识图谱失败: {e}")
            return False

    def _load_json(self) -> None:
        with open(self.storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for e in data.get("entities", []):
            self.add_entity(
                entity_id=e["id"],
                entity_type=EntityType(e["type"]),
                name=e["name"],
                properties=e.get("properties", {}),
                created_at=self._parse_datetime(e.get("created_at")),
                updated_at=self._parse_datetime(e.get("updated_at")),
            )

        for r in data.get("relations", []):
            relation_type = r.get("type", RelationType.RELATED_TO.value)
            try:
                rel_enum = RelationType(relation_type)
            except ValueError:
                rel_enum = RelationType.RELATED_TO
            self.add_relation(
                source_id=r["source"],
                target_id=r["target"],
                relation_type=rel_enum,
                properties=r.get("properties", {}),
                weight=r.get("weight", 1.0),
                created_at=self._parse_datetime(r.get("created_at")),
            )

    def _load_gml(self) -> None:
        self._require_networkx()
        graph = nx.read_gml(self.storage_path)

        for node_id, attrs in graph.nodes(data=True):
            entity_type_value = attrs.get("type", EntityType.TASK.value)
            try:
                entity_type = EntityType(entity_type_value)
            except ValueError:
                entity_type = EntityType.TASK

            raw_props = attrs.get("properties", "{}")
            if isinstance(raw_props, str):
                try:
                    properties = json.loads(raw_props)
                except json.JSONDecodeError:
                    properties = {"raw_properties": raw_props}
            elif isinstance(raw_props, dict):
                properties = raw_props
            else:
                properties = {}

            self.add_entity(
                entity_id=str(node_id),
                entity_type=entity_type,
                name=attrs.get("name", str(node_id)),
                properties=properties,
                created_at=self._parse_datetime(attrs.get("created_at")),
                updated_at=self._parse_datetime(attrs.get("updated_at")),
            )

        for source, target, attrs in graph.edges(data=True):
            rel_type_value = attrs.get("type", RelationType.RELATED_TO.value)
            try:
                rel_type = RelationType(rel_type_value)
            except ValueError:
                rel_type = RelationType.RELATED_TO

            raw_props = attrs.get("properties", "{}")
            if isinstance(raw_props, str):
                try:
                    properties = json.loads(raw_props)
                except json.JSONDecodeError:
                    properties = {"raw_properties": raw_props}
            elif isinstance(raw_props, dict):
                properties = raw_props
            else:
                properties = {}

            self.add_relation(
                source_id=str(source),
                target_id=str(target),
                relation_type=rel_type,
                properties=properties,
                weight=float(attrs.get("weight", 1.0)),
                created_at=self._parse_datetime(attrs.get("created_at")),
            )

    def load(self) -> bool:
        """从文件加载"""
        if not self.storage_path or not self.storage_path.exists():
            return False

        try:
            self._reset()
            if self.storage_format == "gml":
                self._load_gml()
            else:
                self._load_json()
            return True
        except Exception as e:
            print(f"加载知识图谱失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "entity_types": {k.value: len(v) for k, v in self._entity_by_type.items()},
        }


# 导出
__all__ = [
    "KnowledgeGraph",
    "Entity",
    "Relation",
    "EntityType",
    "RelationType",
]

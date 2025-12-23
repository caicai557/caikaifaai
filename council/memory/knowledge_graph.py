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


class RelationType(Enum):
    """关系类型"""
    DEPENDS_ON = "depends_on"       # A 依赖 B
    IMPLEMENTS = "implements"       # A 实现 B
    CONTAINS = "contains"           # A 包含 B
    RELATED_TO = "related_to"       # A 与 B 相关
    DECIDED_BY = "decided_by"       # A 由 B 决定
    APPROVED_BY = "approved_by"     # A 被 B 批准
    CREATED_BY = "created_by"       # A 由 B 创建
    SUPERSEDES = "supersedes"       # A 取代 B


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
    3. 持久化到文件
    
    可扩展为连接 Neo4j / FalkorDB
    
    使用示例:
        kg = KnowledgeGraph()
        
        # 添加实体
        kg.add_entity("file_1", EntityType.FILE, "auth.py", {"path": "src/auth.py"})
        kg.add_entity("decision_1", EntityType.DECISION, "使用JWT认证")
        
        # 添加关系
        kg.add_relation("decision_1", "file_1", RelationType.IMPLEMENTS)
        
        # 查询
        related = kg.get_related("file_1", RelationType.IMPLEMENTS)
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化知识图谱
        
        Args:
            storage_path: 持久化路径
        """
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.storage_path = Path(storage_path) if storage_path else None
        
        # 索引
        self._entity_by_type: Dict[EntityType, Set[str]] = {}
        self._relations_from: Dict[str, List[Relation]] = {}
        self._relations_to: Dict[str, List[Relation]] = {}
    
    def add_entity(
        self, 
        entity_id: str, 
        entity_type: EntityType, 
        name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Entity:
        """
        添加实体
        
        Args:
            entity_id: 实体ID
            entity_type: 实体类型
            name: 实体名称
            properties: 属性
            
        Returns:
            创建的实体
        """
        entity = Entity(
            id=entity_id,
            entity_type=entity_type,
            name=name,
            properties=properties or {},
        )
        self.entities[entity_id] = entity
        
        # 更新索引
        if entity_type not in self._entity_by_type:
            self._entity_by_type[entity_type] = set()
        self._entity_by_type[entity_type].add(entity_id)
        
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
    ) -> Optional[Relation]:
        """
        添加关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 属性
            weight: 权重
            
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
            if entity_type else 
            list(self.entities.values())
        )
        
        for entity in candidates:
            if properties:
                match = all(
                    entity.properties.get(k) == v 
                    for k, v in properties.items()
                )
                if match:
                    results.append(entity)
            else:
                results.append(entity)
        
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
    
    def save(self) -> bool:
        """保存到文件"""
        if not self.storage_path:
            return False
        
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "entities": [e.to_dict() for e in self.entities.values()],
                "relations": [r.to_dict() for r in self.relations],
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存知识图谱失败: {e}")
            return False
    
    def load(self) -> bool:
        """从文件加载"""
        if not self.storage_path or not self.storage_path.exists():
            return False
        
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 清空现有数据
            self.entities.clear()
            self.relations.clear()
            self._entity_by_type.clear()
            self._relations_from.clear()
            self._relations_to.clear()
            
            # 加载实体
            for e in data.get("entities", []):
                self.add_entity(
                    entity_id=e["id"],
                    entity_type=EntityType(e["type"]),
                    name=e["name"],
                    properties=e.get("properties", {}),
                )
            
            # 加载关系
            for r in data.get("relations", []):
                self.add_relation(
                    source_id=r["source"],
                    target_id=r["target"],
                    relation_type=RelationType(r["type"]),
                    properties=r.get("properties", {}),
                    weight=r.get("weight", 1.0),
                )
            
            return True
        except Exception as e:
            print(f"加载知识图谱失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "entity_count": len(self.entities),
            "relation_count": len(self.relations),
            "entity_types": {
                k.value: len(v) 
                for k, v in self._entity_by_type.items()
            },
        }


# 导出
__all__ = [
    "KnowledgeGraph",
    "Entity",
    "Relation",
    "EntityType",
    "RelationType",
]

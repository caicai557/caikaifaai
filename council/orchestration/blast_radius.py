"""
Blast Radius Analyzer - 代码影响分析器

分析代码变更的影响范围 (Blast Radius)，用于智能路由决策。
实现 2025 Best Practice: Impact-Aware Routing

核心概念:
- 入度 (Incoming): 有多少文件导入/依赖此文件
- 叶节点: 入度为 0 的文件 (修改影响小)
- 核心节点: 入度高的文件 (修改影响大)
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from enum import Enum
from pathlib import Path


class ImpactLevel(Enum):
    """影响级别"""
    LEAF = "leaf"          # 叶节点 (无依赖者)
    LOW = "low"            # 低影响 (1-2 依赖者)
    MEDIUM = "medium"      # 中等影响 (3-5 依赖者)
    HIGH = "high"          # 高影响 (6+ 依赖者)
    CORE = "core"          # 核心模块 (10+ 依赖者)


@dataclass
class BlastRadiusResult:
    """影响分析结果"""
    file_path: str
    impact_level: ImpactLevel
    incoming_count: int        # 入度 (依赖此文件的文件数)
    dependents: List[str]      # 依赖此文件的文件列表
    is_core_module: bool       # 是否为核心模块
    requires_full_council: bool  # 是否需要全理事会审议
    reason: str


class BlastRadiusAnalyzer:
    """
    代码影响分析器
    
    通过分析导入关系计算变更的影响范围。
    
    Usage:
        analyzer = BlastRadiusAnalyzer(project_root="/path/to/project")
        result = analyzer.analyze("council/agents/base_agent.py")
        
        if result.impact_level == ImpactLevel.CORE:
            print("⚠️ 核心模块变更，需要全理事会审议")
    """
    
    # 核心模块关键词 (影响加权)
    CORE_KEYWORDS = [
        "base", "core", "common", "utils", "config", "settings",
        "__init__", "main", "app", "api", "auth", "session",
    ]
    
    # 安全敏感路径
    SENSITIVE_PATHS = [
        "auth/", "security/", "governance/", "secrets/",
        ".env", "config/", "credentials",
    ]
    
    def __init__(self, project_root: str = "."):
        """
        初始化分析器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root).resolve()
        self._import_graph: Dict[str, Set[str]] = {}
        self._reverse_graph: Dict[str, Set[str]] = {}
        self._is_built = False
        
    def build_graph(self, scan_dirs: Optional[List[str]] = None) -> None:
        """
        构建导入关系图
        
        Args:
            scan_dirs: 要扫描的目录列表，默认扫描整个项目
        """
        scan_dirs = scan_dirs or ["council", "src"]
        
        for scan_dir in scan_dirs:
            dir_path = self.project_root / scan_dir
            if not dir_path.exists():
                continue
                
            for py_file in dir_path.rglob("*.py"):
                self._analyze_file_imports(py_file)
                
        self._is_built = True
        
    def _analyze_file_imports(self, file_path: Path) -> None:
        """分析单个文件的导入"""
        rel_path = str(file_path.relative_to(self.project_root))
        
        if rel_path not in self._import_graph:
            self._import_graph[rel_path] = set()
            
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return
            
        # 匹配 from X import Y 和 import X
        import_patterns = [
            r"from\s+([\w.]+)\s+import",
            r"^import\s+([\w.]+)",
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imported_module = match.group(1)
                # 转换为可能的文件路径
                possible_paths = self._module_to_paths(imported_module)
                for possible_path in possible_paths:
                    self._import_graph[rel_path].add(possible_path)
                    
                    # 反向图: 记录谁依赖了 possible_path
                    if possible_path not in self._reverse_graph:
                        self._reverse_graph[possible_path] = set()
                    self._reverse_graph[possible_path].add(rel_path)
                    
    def _module_to_paths(self, module: str) -> List[str]:
        """将模块名转换为可能的文件路径"""
        parts = module.split(".")
        paths = []
        
        # council.agents.base -> council/agents/base.py
        file_path = "/".join(parts) + ".py"
        paths.append(file_path)
        
        # council.agents -> council/agents/__init__.py
        dir_path = "/".join(parts) + "/__init__.py"
        paths.append(dir_path)
        
        return paths
        
    def analyze(self, file_path: str) -> BlastRadiusResult:
        """
        分析文件的影响范围
        
        Args:
            file_path: 相对于项目根目录的文件路径
            
        Returns:
            BlastRadiusResult: 影响分析结果
        """
        if not self._is_built:
            self.build_graph()
            
        # 标准化路径
        file_path = file_path.replace("\\", "/")
        
        # 获取入度 (依赖者数量)
        dependents = list(self._reverse_graph.get(file_path, set()))
        incoming_count = len(dependents)
        
        # 检查是否为核心模块 (基于关键词)
        is_core_keyword = any(
            kw in file_path.lower() for kw in self.CORE_KEYWORDS
        )
        
        # 检查是否为安全敏感路径
        is_sensitive = any(
            sens in file_path.lower() for sens in self.SENSITIVE_PATHS
        )
        
        # 计算影响级别
        if incoming_count == 0:
            impact_level = ImpactLevel.LEAF
        elif incoming_count <= 2:
            impact_level = ImpactLevel.LOW
        elif incoming_count <= 5:
            impact_level = ImpactLevel.MEDIUM
        elif incoming_count <= 10:
            impact_level = ImpactLevel.HIGH
        else:
            impact_level = ImpactLevel.CORE
            
        # 关键词加权
        if is_core_keyword and impact_level.value in ["leaf", "low"]:
            impact_level = ImpactLevel.MEDIUM
            
        # 判断是否需要全理事会
        requires_full_council = (
            impact_level in [ImpactLevel.HIGH, ImpactLevel.CORE]
            or is_sensitive
        )
        
        # 生成原因说明
        reasons = []
        if incoming_count > 0:
            reasons.append(f"{incoming_count} 个文件依赖此模块")
        if is_core_keyword:
            reasons.append("核心模块关键词匹配")
        if is_sensitive:
            reasons.append("安全敏感路径")
        if not reasons:
            reasons.append("叶节点，无依赖者")
            
        return BlastRadiusResult(
            file_path=file_path,
            impact_level=impact_level,
            incoming_count=incoming_count,
            dependents=dependents[:10],  # 只返回前 10 个
            is_core_module=is_core_keyword or incoming_count >= 5,
            requires_full_council=requires_full_council,
            reason="; ".join(reasons),
        )
        
    def analyze_multiple(self, file_paths: List[str]) -> BlastRadiusResult:
        """
        分析多个文件的综合影响
        
        返回影响最大的结果
        """
        if not file_paths:
            return BlastRadiusResult(
                file_path="(none)",
                impact_level=ImpactLevel.LEAF,
                incoming_count=0,
                dependents=[],
                is_core_module=False,
                requires_full_council=False,
                reason="无文件变更",
            )
            
        results = [self.analyze(fp) for fp in file_paths]
        
        # 返回影响最大的
        level_order = [ImpactLevel.CORE, ImpactLevel.HIGH, ImpactLevel.MEDIUM, ImpactLevel.LOW, ImpactLevel.LEAF]
        for level in level_order:
            for result in results:
                if result.impact_level == level:
                    result.reason = f"[{len(file_paths)} 个文件中最高影响] " + result.reason
                    return result
                    
        return results[0]
    
    def get_stats(self) -> Dict[str, int]:
        """获取图谱统计"""
        if not self._is_built:
            self.build_graph()
            
        return {
            "total_files": len(self._import_graph),
            "total_edges": sum(len(deps) for deps in self._import_graph.values()),
            "leaf_nodes": sum(1 for f in self._import_graph if f not in self._reverse_graph),
            "core_nodes": sum(1 for f, deps in self._reverse_graph.items() if len(deps) >= 5),
        }


# 导出
__all__ = [
    "BlastRadiusAnalyzer",
    "BlastRadiusResult",
    "ImpactLevel",
]

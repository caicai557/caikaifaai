"""
CodeMap Generator - 代码地图生成器

生成压缩的全库结构图，使模型无需读取全量源码即可感知全局逻辑。

基于 repo-prompt 技能设计。
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import ast


@dataclass
class FileSignature:
    """文件签名"""
    path: str
    size_bytes: int
    classes: List[str]
    functions: List[str]
    imports: List[str]


@dataclass
class CodeMap:
    """代码地图"""
    root_dir: str
    total_files: int
    total_lines: int
    signatures: List[FileSignature]
    dependencies: Dict[str, List[str]]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        lines = [
            f"# 代码地图 - {self.root_dir}",
            "",
            f"> 生成时间: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 概览",
            "",
            f"- 文件总数: {self.total_files}",
            f"- 代码行数: {self.total_lines}",
            "",
            "## 文件结构",
            "",
        ]
        
        for sig in self.signatures[:50]:  # 限制50个
            classes = ", ".join(sig.classes[:3]) or "无"
            funcs = ", ".join(sig.functions[:3]) or "无"
            lines.append(f"### `{sig.path}`")
            lines.append(f"- 类: {classes}")
            lines.append(f"- 函数: {funcs}")
            lines.append("")
        
        return "\n".join(lines)


class CodeMapGenerator:
    """
    代码地图生成器
    
    功能:
    - 扫描项目结构
    - 提取类/函数签名
    - 分析依赖关系
    - 输出压缩结构图
    """
    
    def __init__(
        self,
        root_dir: str = ".",
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ):
        self.root_dir = Path(root_dir)
        self.include_patterns = include_patterns or ["*.py"]
        self.exclude_patterns = exclude_patterns or [
            "__pycache__", ".git", ".venv", "node_modules", "*.egg-info"
        ]
    
    def generate(self) -> CodeMap:
        """生成代码地图"""
        signatures = []
        total_lines = 0
        dependencies = {}
        
        for pattern in self.include_patterns:
            for filepath in self.root_dir.rglob(pattern):
                # 跳过排除目录
                if self._should_exclude(filepath):
                    continue
                
                sig = self._extract_signature(filepath)
                if sig:
                    signatures.append(sig)
                    total_lines += self._count_lines(filepath)
                    
                    # 提取依赖
                    rel_path = str(filepath.relative_to(self.root_dir))
                    dependencies[rel_path] = sig.imports
        
        return CodeMap(
            root_dir=str(self.root_dir),
            total_files=len(signatures),
            total_lines=total_lines,
            signatures=signatures,
            dependencies=dependencies,
        )
    
    def _should_exclude(self, filepath: Path) -> bool:
        """检查是否应排除"""
        path_str = str(filepath)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def _extract_signature(self, filepath: Path) -> Optional[FileSignature]:
        """提取文件签名"""
        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):
                        functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split(".")[0])
            
            return FileSignature(
                path=str(filepath.relative_to(self.root_dir)),
                size_bytes=filepath.stat().st_size,
                classes=classes,
                functions=functions,
                imports=list(set(imports)),
            )
        except Exception:
            return None
    
    def _count_lines(self, filepath: Path) -> int:
        """统计行数"""
        try:
            return len(filepath.read_text(encoding="utf-8").splitlines())
        except Exception:
            return 0
    
    def save(self, output_path: str = "CODEMAP.md") -> str:
        """保存代码地图"""
        codemap = self.generate()
        content = codemap.to_markdown()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return output_path


__all__ = ["CodeMapGenerator", "CodeMap", "FileSignature"]

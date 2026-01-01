"""
CodeMap Skill - 代码地图技能

基于 repo-prompt 最佳实践的代码结构扫描技能。
继承 BaseSkill，支持 HITL 和进度汇报。
"""

from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import ast

from council.skills.base_skill import BaseSkill


@dataclass
class CodeMapOutput:
    """代码地图输出"""
    root_dir: str
    total_files: int
    total_lines: int
    file_signatures: List[Dict[str, Any]]
    markdown: str
    generated_at: datetime = field(default_factory=datetime.now)


class CodeMapSkill(BaseSkill):
    """
    代码地图技能
    
    功能：
    - 扫描项目结构
    - 提取类/函数签名
    - 生成压缩的 Markdown 代码地图
    
    使用示例：
        skill = CodeMapSkill()
        result = await skill.execute("./council", output_path="CODEMAP.md")
    """
    
    def __init__(
        self,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        **kwargs
    ):
        super().__init__(
            name="CodeMap",
            description="生成压缩的代码结构地图，无需读取全量源码即可感知全局逻辑",
            **kwargs
        )
        self.include_patterns = include_patterns or ["*.py"]
        self.exclude_patterns = exclude_patterns or [
            "__pycache__", ".git", ".venv", "node_modules", "*.egg-info"
        ]
    
    async def execute(
        self,
        root_dir: str = ".",
        output_path: Optional[str] = None,
        **kwargs
    ) -> CodeMapOutput:
        """
        执行代码地图扫描
        
        Args:
            root_dir: 扫描根目录
            output_path: 输出文件路径（可选）
            
        Returns:
            CodeMapOutput: 代码地图结果
        """
        root = Path(root_dir)
        signatures = []
        total_lines = 0
        
        # 获取所有匹配文件
        all_files = []
        for pattern in self.include_patterns:
            all_files.extend(root.rglob(pattern))
        
        # 过滤排除项
        files = [f for f in all_files if not self._should_exclude(f)]
        total = len(files)
        
        # 扫描每个文件
        for idx, filepath in enumerate(files):
            await self.report_progress(f"扫描: {filepath.name}", idx, total)
            
            sig = self._extract_signature(root, filepath)
            if sig:
                signatures.append(sig)
                total_lines += sig.get("lines", 0)
        
        # 生成 Markdown
        markdown = self._generate_markdown(root_dir, signatures, total_lines)
        
        # 保存文件
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown)
        
        await self.report_progress("✅ 扫描完成", total, total)
        
        return CodeMapOutput(
            root_dir=root_dir,
            total_files=len(signatures),
            total_lines=total_lines,
            file_signatures=signatures,
            markdown=markdown,
        )
    
    def _should_exclude(self, filepath: Path) -> bool:
        """检查是否排除"""
        path_str = str(filepath)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def _extract_signature(self, root: Path, filepath: Path) -> Optional[Dict[str, Any]]:
        """提取文件签名"""
        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):
                        functions.append(node.name)
            
            return {
                "path": str(filepath.relative_to(root)),
                "classes": classes[:5],  # 限制数量
                "functions": functions[:5],
                "lines": len(content.splitlines()),
            }
        except Exception:
            return None
    
    def _generate_markdown(
        self,
        root_dir: str,
        signatures: List[Dict[str, Any]],
        total_lines: int
    ) -> str:
        """生成 Markdown 代码地图"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        lines = [
            f"# 代码地图 - {root_dir}",
            "",
            f"> 生成时间: {now}",
            "",
            "## 概览",
            "",
            f"- 文件总数: {len(signatures)}",
            f"- 代码行数: {total_lines}",
            "",
            "## 文件结构",
            "",
        ]
        
        for sig in signatures[:50]:  # 限制50个
            classes = ", ".join(sig["classes"]) or "无"
            funcs = ", ".join(sig["functions"]) or "无"
            lines.append(f"### `{sig['path']}`")
            lines.append(f"- 类: {classes}")
            lines.append(f"- 函数: {funcs}")
            lines.append("")
        
        return "\n".join(lines)


__all__ = ["CodeMapSkill", "CodeMapOutput"]

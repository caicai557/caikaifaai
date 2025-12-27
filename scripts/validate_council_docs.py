#!/usr/bin/env python3
"""
AI Council 文档完整性验证工具
检查必需文档是否存在、链接是否有效
"""

from pathlib import Path
import sys


def validate_docs():
    """验证文档完整性"""
    council_dir = Path(".council")
    errors = []
    warnings = []

    # 必需的核心文档
    required_docs = [
        "AGENTS.md",
        "SOP.md",
        "DECISIONS.md",
        "TOKEN_SAVING_PRACTICES.md",
        "MCP_PHILOSOPHY.md",
        "CLAUDE.md",
        "GEMINI.md",
        "CODEX.md",
    ]

    # 检查核心文档
    print("🔍 检查核心文档...")
    for doc in required_docs:
        doc_path = council_dir / doc
        if not doc_path.exists():
            errors.append(f"缺失核心文档: {doc}")
        else:
            size = doc_path.stat().st_size
            if size < 100:
                warnings.append(f"文档过小 ({size} bytes): {doc}")
            print(f"  ✅ {doc} ({size / 1024:.1f} KB)")

    # 检查 prompts 目录
    print("\n🔍 检查 Prompts 模板...")
    prompts_dir = council_dir / "prompts"
    if prompts_dir.exists():
        prompt_files = list(prompts_dir.glob("*.md"))
        print(f"  ✅ 找到 {len(prompt_files)} 个 Prompt 模板")
        for pf in prompt_files:
            print(f"     - {pf.name}")
    else:
        warnings.append("prompts/ 目录不存在")

    # 检查生成的文档
    print("\n🔍 检查生成的文档...")
    docs_dir = council_dir / "docs"
    if docs_dir.exists():
        gen_docs = ["INDEX.md", "BEST_PRACTICES_2025.md", "metadata.json", "README.md"]
        for doc in gen_docs:
            doc_path = docs_dir / doc
            if doc_path.exists():
                print(f"  ✅ {doc}")
            else:
                warnings.append(f"缺失生成文档: {doc}")
    else:
        errors.append("docs/ 目录不存在")

    # 输出结果
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ 发现 {len(errors)} 个错误:")
        for err in errors:
            print(f"  - {err}")

    if warnings:
        print(f"\n⚠️  发现 {len(warnings)} 个警告:")
        for warn in warnings:
            print(f"  - {warn}")

    if not errors and not warnings:
        print("✅ 所有文档验证通过！")

    print("=" * 60)

    return len(errors) == 0


if __name__ == "__main__":
    success = validate_docs()
    sys.exit(0 if success else 1)

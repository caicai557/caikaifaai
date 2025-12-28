# AI Council 开发资料文档

这是自动生成的 AI Council 开发资料文档集合。

## 📂 文档列表

- **INDEX.md** - 完整的文档索引和导航
- **BEST_PRACTICES_2025.md** - 2025 年最新最佳实践汇总
- **metadata.json** - 文档元数据（自动生成）

## 🔄 重新生成文档

使用以下命令重新生成所有文档：

```bash
python3 scripts/generate_docs_v2.py
```

## 📖 如何使用

1. **新手入门**: 先阅读 `INDEX.md` 了解文档结构
2. **最佳实践**: 查看 `BEST_PRACTICES_2025.md` 学习行业实践
3. **深入学习**: 根据 INDEX 导航到具体文档

## 🎯 核心文档路径

```
.council/
├── AGENTS.md              # 治理宪法（必读）
├── CODEMAP.md             # 代码地图
├── SOP.md                 # 标准操作程序
├── DECISIONS.md           # 架构决策日志
├── TOKEN_SAVING_PRACTICES.md  # Token 优化
├── MCP_PHILOSOPHY.md      # MCP 协议理念
├── CLAUDE.md              # Claude 指南
├── GEMINI.md              # Gemini 指南
├── CODEX.md               # Codex 指南
└── docs/                  # 本目录
    ├── INDEX.md           # 索引导航
    ├── BEST_PRACTICES_2025.md
    └── metadata.json
```

## 🤖 自动化维护

该文档集合通过 Python 脚本自动生成，包含：

- 文档元数据收集
- 自动索引生成
- 最佳实践汇总
- 统计信息

**维护者**: AI Council System
**生成器**: `scripts/generate_docs_v2.py`

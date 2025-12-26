---
description: 架构师审计流 (Gemini Pro 2M Context)
---

1. 全库上下文快照
// turbo
./scripts/context_manager.py compact

2. 运行架构审计 Swarm
// turbo
./scripts/council_run.py --task "ARCH-AUDIT" --goal "Audit architecture for: ${argument}" --risk low --learn

3. 生成架构决策记录 (ADR)

> 请根据审计结果，在 `.council/DECISIONS.md` 中追加新的 ADR 条目。
> 格式参考: `## ADR-00X: [Title]`

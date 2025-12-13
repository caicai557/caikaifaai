---
description: 翻译子系统落地（Google 翻译：缓存/限流/失败策略）
argument-hint: [source->target 例如 auto->zh 或 zh->en]
---
为“$ARGUMENTS”输出翻译子系统工程方案（不写代码）：
- 推荐实现路径（优先 Cloud Translation API；若网页翻译则必须标注不稳定风险）
- 接口契约：translate(text, source?, target, meta) -> {translatedText, detectedSource?, latencyMs, provider}
- 超时/重试/限流/缓存（cacheKey、TTL、命中率指标）
- 失败策略（fallback/人工接管/原文直通三选一并写死）
- 验收 ≥ 10 条（失败率、P95 延迟、缓存命中率等）

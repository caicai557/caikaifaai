#!/bin/bash
# audit_gemini.sh - 调用 Gemini 进行全库审计

set -e

echo "=== Gemini Auditor ==="
echo ""
echo "触发条件 (满足任一才用):"
echo "- [ ] 影响 ≥3 模块"
echo "- [ ] 接口契约不确定"
echo "- [ ] 不确定\"改 A 会不会炸 B\""
echo ""
echo "请将以下 prompt 粘贴到 Gemini CLI:"
echo ""
cat <<EOF
You are the Auditor.
Inputs: SPEC.md + CODEMAP.md.
Goal: find cross-file conflicts, missing edge cases, API contract issues.

Output AUDIT.md:
- Conflicts / integration risks
- Contract clarifications (errors, types)
- Test strategy (what must be covered)
- Minimal revisions to SPEC (if needed)
EOF

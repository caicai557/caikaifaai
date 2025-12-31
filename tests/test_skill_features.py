import pytest
import asyncio
from council.skills.security_audit_skill import SecurityAuditSkill


@pytest.mark.asyncio
async def test_security_audit_hitl_and_streaming(tmp_path):
    # 1. 设置环境：创建一个包含 Critical 漏洞的文件
    (tmp_path / ".env").write_text("API_KEY='sk-1234567890123456'")

    # 2. 定义回调
    progress_updates = []
    approval_requests = []

    async def on_progress(msg, current, total):
        progress_updates.append((msg, current, total))

    async def on_approval(action, context):
        approval_requests.append((action, context))
        return True  # 批准

    # 3. 初始化 Skill
    skill = SecurityAuditSkill(
        working_dir=str(tmp_path),
        progress_callback=on_progress,
        approval_callback=on_approval,
    )

    # 4. 执行
    result = await skill.execute(target_dir=".")

    # 5. 验证 Streaming
    assert len(progress_updates) > 0
    assert progress_updates[0][0] == "开始安全审计..."
    assert progress_updates[-1][0] == "审计完成"

    # 6. 验证 HITL
    # 因为有 .env 文件，应该触发 Critical 告警
    assert len(approval_requests) == 1
    action, context = approval_requests[0]
    assert action == "critical_findings_found"
    assert context["count"] > 0

    print("\n✅ HITL and Streaming tests passed")

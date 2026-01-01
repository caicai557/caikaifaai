"""
SessionStart Hook - 会话启动钩子

在理事会会话启动时触发，负责环境初始化和状态恢复。
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from council.hooks.base import (
    BaseHook,
    HookType,
    HookAction,
    HookResult,
    HookContext,
)

logger = logging.getLogger(__name__)


class SessionStartHook(BaseHook):
    """
    会话启动钩子

    功能：
    1. 执行 init.sh 初始化脚本
    2. 激活虚拟环境
    3. 安装依赖
    4. 注入受控环境变量
    5. 恢复跨会话状态

    Usage:
        hook = SessionStartHook(working_dir="/path/to/project")
        result = await hook.execute(context)
    """

    def __init__(
        self,
        working_dir: str = ".",
        state_file: str = ".council/session_state.json",
        init_script: str = "init.sh",
        env_file: str = ".env",
        priority: int = 10,
    ):
        """
        初始化会话启动钩子

        Args:
            working_dir: 工作目录
            state_file: 状态持久化文件路径
            init_script: 初始化脚本名称
            env_file: 环境变量文件
            priority: 优先级
        """
        super().__init__(name="session_start", priority=priority)
        self.working_dir = Path(working_dir).resolve()
        self.state_file = self.working_dir / state_file
        self.init_script = self.working_dir / init_script
        self.env_file = self.working_dir / env_file
        self._state: Dict[str, Any] = {}

    @property
    def hook_type(self) -> HookType:
        return HookType.SESSION_START

    async def execute(self, context: HookContext) -> HookResult:
        """
        执行会话初始化

        Args:
            context: 钩子上下文

        Returns:
            HookResult: 初始化结果
        """
        metadata: Dict[str, Any] = {
            "session_id": context.session_id,
            "steps_completed": [],
        }

        try:
            # Step 1: 恢复跨会话状态
            await self._restore_state()
            metadata["steps_completed"].append("restore_state")
            metadata["restored_state"] = bool(self._state)

            # Step 2: 加载环境变量
            env_loaded = await self._load_env_vars()
            metadata["steps_completed"].append("load_env")
            metadata["env_loaded"] = env_loaded

            # Step 3: 执行初始化脚本
            if self.init_script.exists():
                script_result = await self._run_init_script()
                metadata["steps_completed"].append("init_script")
                metadata["init_script_result"] = script_result
            else:
                metadata["init_script_skipped"] = True

            # Step 4: 检查虚拟环境
            venv_active = self._check_venv()
            metadata["steps_completed"].append("check_venv")
            metadata["venv_active"] = venv_active

            logger.info(f"Session initialized: {context.session_id}")
            return HookResult(
                action=HookAction.ALLOW,
                message="Session initialized successfully",
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Session initialization failed: {e}")
            return HookResult(
                action=HookAction.ALLOW,  # 允许继续，但记录错误
                message=f"Session initialization completed with warnings: {e}",
                error=str(e),
                metadata=metadata,
            )

    async def _restore_state(self) -> None:
        """恢复跨会话状态"""
        if self.state_file.exists():
            try:
                content = self.state_file.read_text()
                self._state = json.loads(content)
                logger.info(f"Restored state from {self.state_file}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse state file: {e}")
                self._state = {}

    async def save_state(self) -> None:
        """保存会话状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state, indent=2))
        logger.info(f"State saved to {self.state_file}")

    def set_state(self, key: str, value: Any) -> None:
        """设置状态值"""
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        return self._state.get(key, default)

    async def _load_env_vars(self) -> int:
        """
        加载环境变量（受控注入）

        Returns:
            加载的变量数量
        """
        if not self.env_file.exists():
            return 0

        count = 0
        try:
            content = self.env_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    # 安全检查：不覆盖敏感系统变量
                    if key.upper() not in {"PATH", "HOME", "USER", "SHELL"}:
                        os.environ[key] = value
                        count += 1
            logger.info(f"Loaded {count} environment variables from {self.env_file}")
        except Exception as e:
            logger.warning(f"Failed to load env file: {e}")

        return count

    async def _run_init_script(self) -> Dict[str, Any]:
        """
        执行初始化脚本

        Returns:
            脚本执行结果
        """
        try:
            # 使用 asyncio 子进程执行
            process = await asyncio.create_subprocess_exec(
                "bash",
                str(self.init_script),
                cwd=str(self.working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode()[-500:] if stdout else "",  # 限制输出长度
                "stderr": stderr.decode()[-500:] if stderr else "",
                "success": process.returncode == 0,
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Script timed out after 60s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_venv(self) -> bool:
        """检查虚拟环境是否激活"""
        return bool(os.environ.get("VIRTUAL_ENV"))


# 导出
__all__ = ["SessionStartHook"]

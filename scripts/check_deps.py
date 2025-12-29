#!/usr/bin/env python3
"""
检查依赖和登录状态

用途: just check
"""

import subprocess
import sys
import shutil
from pathlib import Path


def print_status(name: str, ok: bool, message: str = "") -> bool:
    """打印检查状态"""
    icon = "✅" if ok else "❌"
    msg = f" - {message}" if message else ""
    print(f"{icon} {name}{msg}")
    return ok


def check_python() -> bool:
    """检查 Python 版本"""
    version = sys.version_info
    ok = version >= (3, 12)
    return print_status(
        "Python version",
        ok,
        f"{version.major}.{version.minor}.{version.micro}"
        + ("" if ok else " (需要 3.12+)"),
    )


def check_package(name: str) -> bool:
    """检查包是否安装"""
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def check_packages() -> bool:
    """检查必需的包"""
    required = ["council", "pytest"]
    optional = ["chromadb", "aiosqlite"]

    all_ok = True
    for pkg in required:
        ok = check_package(pkg)
        all_ok = all_ok and ok
        print_status(f"Package: {pkg}", ok, "installed" if ok else "MISSING")

    for pkg in optional:
        ok = check_package(pkg)
        print_status(
            f"Package: {pkg} (optional)", ok, "installed" if ok else "not installed"
        )

    return all_ok


def check_command(cmd: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(cmd) is not None


def check_claude_auth() -> bool:
    """检查 Claude 认证状态"""
    if not check_command("claude"):
        return print_status("Claude CLI", False, "not installed")

    try:
        subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=5,
        )
        # 如果能运行就算认证成功（简化检查）
        return print_status("Claude CLI", True, "installed")
    except Exception as e:
        return print_status("Claude CLI", False, str(e))


def check_gemini_auth() -> bool:
    """检查 Gemini 认证状态"""
    if not check_command("gemini"):
        return print_status("Gemini CLI", False, "not installed (optional)")

    return print_status("Gemini CLI", True, "installed")


def check_just() -> bool:
    """检查 just 是否安装"""
    ok = check_command("just")
    return print_status(
        "Just (task runner)", ok, "installed" if ok else "run: cargo install just"
    )


def check_git() -> bool:
    """检查 Git 和仓库状态"""
    if not check_command("git"):
        return print_status("Git", False, "not installed")

    # 检查是否在 git 仓库中
    git_dir = Path(".git")
    if git_dir.exists():
        return print_status("Git", True, "repository detected")
    else:
        return print_status("Git", False, "not in a git repository")


def main() -> int:
    """主函数"""
    print("=" * 50)
    print("  Council Setup Check")
    print("=" * 50)
    print()

    checks = [
        check_python(),
        check_packages(),
        check_claude_auth(),
        check_gemini_auth(),
        check_just(),
        check_git(),
    ]

    print()

    if all(checks):
        print("🎉 All checks passed! Ready to develop.")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        print("Quick fixes:")
        print("  - Install packages: pip install -e '.[dev]'")
        print("  - Login Claude:     claude login")
        print("  - Login Gemini:     gemini (select Login with Google)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

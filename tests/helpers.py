"""
Helper functions for testing.
"""



def detect_legacy_params():
    """Detect legacy CLI parameters and show migration message.

    Checks sys.argv for legacy parameters and shows migration guide if found.
    Exits with code 1 if legacy parameters are detected.
    """
    import sys

    # Legacy parameters that were used in old CLI
    legacy_params = {'--instances', '-n', '--source', '-s'}

    # Check if any arguments match legacy parameters
    # Skip the first argument (script name)
    if len(sys.argv) > 1:
        # Look for legacy params in arguments
        for arg in sys.argv[1:]:
            if arg in legacy_params:
                # Print migration message
                print("⚠️  旧 CLI 参数已弃用。请使用新命令:")
                print()
                print("快速启动命令:")
                print("  python run_telegram.py launch --all")
                print("  python run_telegram.py --config telegram.yaml launch --all")
                print()
                print("示例配置文件 (telegram.yaml):")
                print("  instances:")
                print("    - id: account1")
                print("      profile_path: ~/.telegram_profiles/account1")
                print("    - id: account2")
                print("      profile_path: ~/.telegram_profiles/account2")
                print()
                print("更多信息请参考: README.md")

                # Exit with error code
                sys.exit(1)

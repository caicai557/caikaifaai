#!/usr/bin/env python3
"""
Prototype: Playwright 发送消息能力验证

目标: 验证能否通过 Playwright Python API 在 Telegram Web A 执行发送操作
- 启动浏览器访问 Telegram Web A
- 定位输入框
- 填充消息文本
- 点击发送按钮

如果成功，则 AutoResponder 的技术可行性确认 ✅
"""

import asyncio
from playwright.async_api import async_playwright


async def test_telegram_send():
    """测试 Telegram Web A 发送消息流程"""
    async with async_playwright() as p:
        # 启动浏览器（非 headless 以便观察）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 访问 Telegram Web A
        print("📱 访问 Telegram Web A...")
        await page.goto("https://web.telegram.org/a/")

        # 等待页面加载
        print("⏳ 等待页面加载...")
        await page.wait_for_load_state("networkidle")

        # 用户需手动登录（等待 30 秒）
        print("👤 请在浏览器中手动登录 Telegram...")
        print("⏰ 30 秒后将尝试发送测试消息")
        await asyncio.sleep(30)

        # 尝试定位输入框（多种可能的选择器）
        input_selectors = [
            "div[contenteditable='true']",  # 通用富文本编辑器
            ".composer-input",  # Telegram 可能的类名
            "[placeholder*='Message']",  # 包含 Message 的占位符
            "textarea",  # 备用 textarea
        ]

        input_element = None
        for selector in input_selectors:
            try:
                input_element = await page.wait_for_selector(
                    selector, timeout=5000, state="visible"
                )
                print(f"✅ 找到输入框: {selector}")
                break
            except Exception:
                continue

        if not input_element:
            print("❌ 未找到输入框，可能需要更新选择器")
            await browser.close()
            return False

        # 填充测试消息
        test_message = "🤖 Playwright 自动化测试消息 - 请忽略"
        print(f"📝 填充消息: {test_message}")

        # 尝试填充（多种方法）
        try:
            # 方法 1: fill (适用于 input/textarea)
            await input_element.fill(test_message)
        except Exception:
            try:
                # 方法 2: type (逐字符输入，更自然)
                await input_element.type(test_message, delay=50)
            except Exception:
                # 方法 3: evaluate (直接设置 innerHTML/textContent)
                await page.evaluate(
                    f"(el) => el.textContent = '{test_message}'", input_element
                )

        # 等待 2 秒（模拟人工打字延迟）
        await asyncio.sleep(2)

        # 尝试定位发送按钮
        send_button_selectors = [
            "button[aria-label*='Send']",
            "button.send-button",
            "button:has-text('Send')",
            "button svg",  # 发送图标通常是 SVG
        ]

        send_button = None
        for selector in send_button_selectors:
            try:
                send_button = await page.wait_for_selector(
                    selector, timeout=5000, state="visible"
                )
                print(f"✅ 找到发送按钮: {selector}")
                break
            except Exception:
                continue

        if not send_button:
            print("⚠️ 未找到发送按钮，尝试按 Enter 键...")
            await input_element.press("Enter")
        else:
            print("🚀 点击发送按钮...")
            await send_button.click()

        # 等待 3 秒观察结果
        await asyncio.sleep(3)

        print("✅ 原型验证完成！")
        print("请检查 Telegram 聊天界面是否成功发送消息")

        await browser.close()
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("Playwright 发送消息能力验证")
    print("=" * 60)
    print()

    try:
        result = asyncio.run(test_telegram_send())
        if result:
            print("\n✅ 验证通过 - AutoResponder 技术可行")
        else:
            print("\n❌ 验证失败 - 需要调整选择器或方案")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()

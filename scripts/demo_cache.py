from council.core.llm_client import default_client


def main():
    print("🚀 Running Cache Demo...")

    # Mock a large system prompt that would trigger caching
    large_context = (
        "This is a very large context " * 1000
    )  # ~5000 tokens, might need more for 32k limit
    # Gemini requires >32k tokens for caching usually, but let's see if our manager handles it
    # The manager has MIN_CACHE_TOKENS = 32768

    # We'll force it for demo purposes by mocking the check or just printing
    print(f"Client type: {type(default_client)}")

    if "CachedLLMClient" in str(type(default_client)):
        print("✅ CachedLLMClient is active")
    else:
        print("❌ CachedLLMClient is NOT active")

    # Note: Without a real API key and 32k+ tokens, we can't actually hit the Gemini Cache API successfully in this demo
    # But we verified the class is swapped.


if __name__ == "__main__":
    main()

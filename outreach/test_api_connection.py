"""
test_api_connection.py — Diagnose Anthropic API connectivity issues.

Run this BEFORE test_agent.py to confirm your API key and network connection work.

Usage:
  python outreach/test_api_connection.py
  python outreach/test_api_connection.py --key sk-ant-api03-your-key-here
"""

import argparse
import os
import socket
import ssl
import sys


def check_dns():
    print("\n[1] DNS resolution — api.anthropic.com")
    try:
        ip = socket.gethostbyname("api.anthropic.com")
        print(f"    ✓ Resolved to {ip}")
        return True
    except Exception as e:
        print(f"    ✗ DNS failed: {e}")
        print("      → Check your internet connection or DNS settings")
        return False


def check_https():
    print("\n[2] HTTPS connection — api.anthropic.com:443")
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection(("api.anthropic.com", 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname="api.anthropic.com") as ssock:
                print(f"    ✓ TLS connected (protocol: {ssock.version()})")
                return True
    except ssl.SSLError as e:
        print(f"    ✗ SSL error: {e}")
        print("      → Try: pip install --upgrade certifi")
        return False
    except Exception as e:
        print(f"    ✗ Connection failed: {e}")
        print("      → Firewall or antivirus may be blocking Python's HTTPS")
        return False


def check_anthropic_sdk(api_key: str):
    print("\n[3] Anthropic SDK — minimal API call")
    try:
        import anthropic
        import httpx
    except ImportError as e:
        print(f"    ✗ missing package: {e} — pip install anthropic httpx")
        return False

    # First try: default (respects Windows system proxy settings)
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say: OK"}],
        )
        reply = msg.content[0].text.strip()
        print(f"    ✓ API responded: {reply!r}")
        return True
    except (anthropic.APIConnectionError, Exception) as first_err:
        print(f"    ~ Default client failed: {type(first_err).__name__}")

    # Second try: bypass Windows proxy settings entirely
    print("    ~ Retrying with proxy bypassed (trust_env=False)...")
    try:
        http_client = httpx.Client(trust_env=False)
        client = anthropic.Anthropic(api_key=api_key, http_client=http_client)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say: OK"}],
        )
        reply = msg.content[0].text.strip()
        print(f"    ✓ API responded (proxy bypassed): {reply!r}")
        print("    ! FIX: Windows proxy is blocking httpx.")
        print("      Run this once, then open a new CMD window:")
        print("        setx NO_PROXY \"*\"")
        return True
    except anthropic.AuthenticationError:
        print("    ✗ Authentication error — API key is invalid or expired")
        print("      → Get a fresh key at: console.anthropic.com")
        return False
    except Exception as e:
        print(f"    ✗ Both attempts failed: {e}")
        return False


def check_langchain_anthropic(api_key: str):
    print("\n[4] LangChain Anthropic — minimal call (what browser-use uses)")
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage
    except ImportError:
        print("    ✗ langchain-anthropic not installed: pip install langchain-anthropic")
        return False

    try:
        llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=api_key,
            max_tokens=10,
        )
        result = llm.invoke([HumanMessage(content="Say: OK")])
        print(f"    ✓ LangChain responded: {result.content!r}")
        return True
    except Exception as e:
        print(f"    ✗ LangChain call failed: {e}")
        return False


def suggest_proxy_fix():
    print("\n--- PROXY WORKAROUND ---")
    print("If you're on a corporate network or Windows with strict outbound rules:")
    print("")
    print("  Option A: Use environment variable proxy")
    print("    set HTTPS_PROXY=http://proxy-server:8080")
    print("")
    print("  Option B: Run on a VPS (RunPod, DigitalOcean, etc.)")
    print("    The pipeline is designed to run on a server anyway.")
    print("    Linux VPS + Playwright headless = no browser window needed.")
    print("")
    print("  Option C: Use local Ollama model (zero API cost, zero connectivity needed)")
    print("    ollama pull qwen2.5:7b")
    print("    python outreach/run_campaign.py ... --local-model")
    print("    python outreach/test_agent.py --url https://example.com/contact --local-model")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnose Anthropic API connectivity")
    parser.add_argument("--key", help="API key to test (falls back to ANTHROPIC_API_KEY env var)")
    args = parser.parse_args()

    api_key = args.key or os.environ.get("ANTHROPIC_API_KEY", "")

    print("=" * 60)
    print("  Anthropic API Connection Diagnostic")
    print("=" * 60)

    if not api_key or api_key == "your_key_here":
        print("\n✗ No valid API key found.")
        print("  Set it: set ANTHROPIC_API_KEY=sk-ant-api03-...")
        print("  Or pass: python outreach/test_api_connection.py --key sk-ant-api03-...")
        sys.exit(1)

    print(f"\n  Key: {api_key[:20]}...{api_key[-4:]}")

    dns_ok = check_dns()
    tls_ok = check_https() if dns_ok else False
    sdk_ok = check_anthropic_sdk(api_key) if tls_ok else False
    lc_ok  = check_langchain_anthropic(api_key) if tls_ok else False

    print("\n" + "=" * 60)
    print("  Results")
    print("=" * 60)
    print(f"  DNS:             {'✓' if dns_ok else '✗'}")
    print(f"  TLS/HTTPS:       {'✓' if tls_ok else '✗'}")
    print(f"  Anthropic SDK:   {'✓' if sdk_ok else '✗'}")
    print(f"  LangChain:       {'✓' if lc_ok else '✗'}")

    if dns_ok and tls_ok and sdk_ok and lc_ok:
        print("\n  ✓ ALL CHECKS PASSED — run test_agent.py now")
    else:
        suggest_proxy_fix()

    sys.exit(0 if (sdk_ok and lc_ok) else 1)

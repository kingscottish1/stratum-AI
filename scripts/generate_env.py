#!/usr/bin/env python3
"""Stratum AI - generate .env from .env.example with fresh secrets.

Cross-platform (Windows / Linux / macOS). Creates .env only if it does
not already exist. Defaults to DEMO_MODE=true so you can test instantly;
set DEMO_MODE=false (and add your LLM key) for real mode.
"""
import pathlib
import re
import secrets
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / ".env.example"
DEST = ROOT / ".env"


def main() -> int:
    if DEST.exists():
        print("[skip] .env already exists - keeping it (delete it to regenerate).")
        return 0
    if not EXAMPLE.exists():
        print("[error] .env.example not found next to the installer.")
        return 1

    text = EXAMPLE.read_text(encoding="utf-8")

    # fresh secrets - nothing hardcoded, nothing shared
    replacements = {
        r"^JWT_SECRET=.*$": f"JWT_SECRET={secrets.token_hex(32)}",
        r"^ENCRYPTION_KEY=.*$": f"ENCRYPTION_KEY={secrets.token_hex(32)}",
        r"^DEMO_ADMIN_PASSWORD=.*$": f"DEMO_ADMIN_PASSWORD={secrets.token_urlsafe(16)}",
    }
    for pattern, value in replacements.items():
        text = re.sub(pattern, value, text, flags=re.MULTILINE)

    # easy testing: demo mode ON by default (owner-testing only)
    text = text.replace("DEMO_MODE=false", "DEMO_MODE=true")

    DEST.write_text(text, encoding="utf-8")
    print("[ok] .env created with fresh JWT_SECRET + ENCRYPTION_KEY.")
    print("     DEMO_MODE=true (testing only). Everything else stays real.")
    print("     To bring your own LLM, edit .env and set:")
    print("       LLM_PROVIDER=openai        # or anthropic/azure/groq/...")
    print("       LLM_API_KEY=sk-...")
    print("     For real mode: set DEMO_MODE=false, then restart.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

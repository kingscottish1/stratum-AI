#!/usr/bin/env python3
"""
Stratum AI — unified demo runner (OWNER TESTING ONLY).

Runs the real vertical agent suites against in-memory mocks. Requires
DEMO_MODE=true (or pass --force) — everything else in the platform is real.

Examples:
  python3 DEMOS/run_demo.py all
  python3 DEMOS/run_demo.py clinic --interactive
  python3 DEMOS/run_demo.py realestate
  python3 DEMOS/run_demo.py logistics
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BANNER = (
    "\n  ⚠️  DEMO MODE — in-memory mocks, owner testing only.\n"
    "     Production refuses to load these (STRATUM_ENV=production).\n"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stratum AI runnable demos (owner testing)")
    parser.add_argument("vertical", choices=["clinic", "realestate", "logistics", "all"])
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="run even when DEMO_MODE is not set")
    args = parser.parse_args()

    demo_enabled = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")
    if not demo_enabled and not args.force:
        print("DEMO MODE is off. Set DEMO_MODE=true in .env (owner testing only)")
        print("or re-run with --force.")
        sys.exit(1)
    print(BANNER)
    print("Built by kingscottishDEV · N.A.S — Nexus Audit Security\n")

    selected = ["clinic", "realestate", "logistics"] if args.vertical == "all" else [args.vertical]
    for name in selected:
        if name == "clinic":
            from DEMOS.demo_clinic import main as demo
        elif name == "realestate":
            from DEMOS.demo_realestate import main as demo
        else:
            from DEMOS.demo_logistics import main as demo
        demo(interactive=args.interactive)
        if name != selected[-1]:
            print()


if __name__ == "__main__":
    main()

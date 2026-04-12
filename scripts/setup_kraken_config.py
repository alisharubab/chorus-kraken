"""
Task 1 -- Configure Kraken CLI from .env

This script:
1. Loads KRAKEN_API_KEY and KRAKEN_API_SECRET from .env
2. Creates ~/.config/kraken/ if needed
3. Writes ~/.config/kraken/config.toml
4. Verifies the CLI config by running: kraken balance -o json
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _masked(value: str) -> str:
    """Hide most credential characters when printing to terminal."""
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:6]}...{value[-4:]}"


def main() -> int:
    api_key = os.getenv("KRAKEN_API_KEY", "")
    api_secret = os.getenv("KRAKEN_API_SECRET", "")

    print("[STEP 1] Reading Kraken credentials from .env ...")
    if not api_key or not api_secret:
        print("[FAIL] Missing KRAKEN_API_KEY or KRAKEN_API_SECRET in .env")
        return 1
    print(f"[OK] API key found: {_masked(api_key)}")
    print(f"[OK] API secret found: {_masked(api_secret)}")

    print("\n[STEP 2] Creating Kraken config directory ...")
    config_dir = Path.home() / ".config" / "kraken"
    config_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directory ready: {config_dir}")

    print("\n[STEP 3] Writing config.toml ...")
    config_path = config_dir / "config.toml"
    config_text = (
        "[auth]\n"
        f'api_key = "{api_key}"\n'
        f'api_secret = "{api_secret}"\n'
    )
    config_path.write_text(config_text, encoding="utf-8")
    print(f"[OK] Config written: {config_path}")

    print("\n[STEP 4] Verifying with: wsl kraken balance -o json")
    try:
        result = subprocess.run(
            ["wsl", "kraken", "balance", "-o", "json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            # Fallback for WSL shells where PATH is only set in bash startup files.
            result = subprocess.run(
                ["wsl", "bash", "-lc", "kraken balance -o json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
    except FileNotFoundError:
        print("[FAIL] Could not execute `wsl kraken ...`.")
        print("       Ensure WSL is installed and Kraken CLI is available inside Ubuntu.")
        return 1
    except subprocess.TimeoutExpired:
        print("[FAIL] Kraken balance command timed out after 30s.")
        return 1

    if result.returncode != 0:
        print(f"[FAIL] Kraken CLI returned non-zero exit code: {result.returncode}")
        if result.stderr.strip():
            print("       stderr:")
            print(result.stderr.strip())
        if result.stdout.strip():
            print("       stdout:")
            print(result.stdout.strip())
        return 1

    stdout = result.stdout.strip()
    print("[OK] Kraken CLI command succeeded.")
    try:
        parsed = json.loads(stdout) if stdout else {}
        print("[INFO] Parsed balance JSON:")
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print("[WARN] Output was not valid JSON. Raw output below:")
        print(stdout)

    print("\n[DONE] Kraken CLI configuration is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

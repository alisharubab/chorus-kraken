"""
Task 2 -- CHORUS end-to-end cycle test

This script verifies:
1. Each sub-agent returns a valid signed vote
2. Risk Sentinel veto behavior when daily PnL is forced to -3%
3. One full meta-agent cycle runs
4. A decision artifact JSON is created in /artifacts
5. Artifact hash logging to ValidationRegistry works on-chain
6. Kraken CLI paper trade command can be called through WSL

Usage:
  python scripts/test_cycle.py
"""
import glob
import json
import os
import subprocess
import sys
import time
from typing import Dict, Tuple

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENTS_DIR = os.path.join(PROJECT_ROOT, "agents")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")
DAILY_PNL_FILE = os.path.join(PROJECT_ROOT, "daily_pnl.json")

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

PASS = "PASS"
FAIL = "FAIL"

results = []
context = {
    "latest_decision_file": None,
    "cycle_result": None,
}


def record(step: str, ok: bool, detail: str):
    status = PASS if ok else FAIL
    safe_detail = str(detail).encode("ascii", "backslashreplace").decode("ascii")
    results.append((status, step, detail))
    print(f"[{status}] {step}: {safe_detail}")


def _vote_error(vote: Dict) -> str:
    required_fields = ["agent_id", "direction", "confidence", "signature"]
    for field in required_fields:
        if field not in vote:
            return f"missing required field '{field}'"

    if vote["direction"] not in ["BUY", "SELL", "HOLD", "PROCEED"]:
        return f"invalid direction '{vote['direction']}'"

    try:
        confidence = int(vote["confidence"])
    except Exception:
        return f"confidence is not numeric: {vote['confidence']}"

    if confidence < 0 or confidence > 100:
        return f"confidence out of range (0-100): {confidence}"

    signature = str(vote["signature"])
    if not signature.startswith("0x") or len(signature) < 20:
        return "signature format looks invalid"

    return ""


def _get_validation_contract():
    from utils import w3, CONTRACTS

    if not CONTRACTS.get("validation"):
        raise RuntimeError("Validation contract address missing in contract_addresses.json")

    abi = [
        {
            "inputs": [{"name": "agentId", "type": "uint256"}],
            "name": "getArtifactCount",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [
                {"name": "", "type": "uint256"},
                {"name": "", "type": "uint256"},
            ],
            "name": "agentArtifacts",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [{"name": "", "type": "uint256"}],
            "name": "artifacts",
            "outputs": [
                {"name": "artifactId", "type": "uint256"},
                {"name": "agentId", "type": "uint256"},
                {"name": "artifactType", "type": "string"},
                {"name": "dataHash", "type": "bytes32"},
                {"name": "timestamp", "type": "uint256"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS["validation"]),
        abi=abi,
    )
    return w3, contract


def step_validate_subagent_votes() -> Tuple[bool, str]:
    from trend_agent import analyze as trend_analyze
    from reversal_agent import analyze as reversal_analyze
    from sentiment_agent import analyze as sentiment_analyze
    from risk_sentinel import analyze as risk_analyze

    votes = [
        trend_analyze("XBTUSD"),
        reversal_analyze("XBTUSD"),
        sentiment_analyze("XBTUSD"),
        risk_analyze("XBTUSD"),
    ]

    for vote in votes:
        err = _vote_error(vote)
        if err:
            return False, f"{vote.get('agent_name', 'unknown_agent')} vote invalid: {err}"

    summary = ", ".join(f"{v['agent_name']}={v['direction']}({v['confidence']}%)" for v in votes)
    return True, summary


def step_verify_risk_veto() -> Tuple[bool, str]:
    from risk_sentinel import analyze as risk_analyze
    from meta_agent import tally_votes

    original_exists = os.path.exists(DAILY_PNL_FILE)
    original_content = None
    if original_exists:
        with open(DAILY_PNL_FILE, "r", encoding="utf-8") as f:
            original_content = f.read()

    try:
        with open(DAILY_PNL_FILE, "w", encoding="utf-8") as f:
            json.dump({"pnl_percent": -3.0}, f)

        risk_vote = risk_analyze("XBTUSD")
        if risk_vote.get("direction") != "HOLD":
            return False, f"expected HOLD veto at -3.0%, got {risk_vote.get('direction')}"

        mock_votes = [
            {
                "agent_id": 1,
                "agent_name": "TrendAgent",
                "direction": "BUY",
                "confidence": 90,
                "signature": "0xmock",
            },
            {
                "agent_id": 2,
                "agent_name": "ReversalAgent",
                "direction": "SELL",
                "confidence": 80,
                "signature": "0xmock",
            },
            risk_vote,
            {
                "agent_id": 4,
                "agent_name": "SentimentAgent",
                "direction": "BUY",
                "confidence": 75,
                "signature": "0xmock",
            },
        ]

        tally = tally_votes(mock_votes)
        if tally.get("decision") != "HOLD":
            return False, f"expected final HOLD due to veto, got {tally.get('decision')}"

        return True, f"Risk veto confirmed: {risk_vote.get('reason', 'no reason provided')}"
    finally:
        if original_exists:
            with open(DAILY_PNL_FILE, "w", encoding="utf-8") as f:
                f.write(original_content)
        elif os.path.exists(DAILY_PNL_FILE):
            os.remove(DAILY_PNL_FILE)


def step_run_meta_cycle() -> Tuple[bool, str]:
    from meta_agent import run_cycle

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    before = set(glob.glob(os.path.join(ARTIFACTS_DIR, "decision_*.json")))

    result = run_cycle("XBTUSD")

    after = set(glob.glob(os.path.join(ARTIFACTS_DIR, "decision_*.json")))
    new_files = sorted(list(after - before), key=os.path.getmtime)
    if not new_files:
        return False, "meta_agent.run_cycle() completed but no new decision_*.json created"

    latest = new_files[-1]
    context["latest_decision_file"] = latest
    context["cycle_result"] = result

    return True, f"Decision={result.get('decision')} | artifact={os.path.basename(latest)}"


def step_verify_artifact_saved() -> Tuple[bool, str]:
    latest = context.get("latest_decision_file")
    if not latest:
        return False, "no decision artifact path in context"
    if not os.path.exists(latest):
        return False, f"artifact file missing: {latest}"

    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)

    required = ["type", "pair", "votes", "decision", "timestamp"]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"artifact missing keys: {', '.join(missing)}"

    return True, f"artifact JSON valid at {latest}"


def step_verify_hash_logged_onchain() -> Tuple[bool, str]:
    from artifact_logger import log_artifact_onchain
    from utils import hash_artifact

    w3, contract = _get_validation_contract()

    test_agent_id = 9999
    test_artifact = {
        "type": "TEST_CYCLE_HASH_CHECK",
        "source": "scripts/test_cycle.py",
        "timestamp": int(time.time()),
    }

    expected_hash_hex = "0x" + hash_artifact(test_artifact)
    before_count = contract.functions.getArtifactCount(test_agent_id).call()

    tx_hash = log_artifact_onchain(test_agent_id, "TEST_CYCLE_HASH_CHECK", test_artifact)
    if not tx_hash:
        return False, "log_artifact_onchain returned no tx hash"

    after_count = contract.functions.getArtifactCount(test_agent_id).call()
    if after_count != before_count + 1:
        return False, f"artifact count did not increment (before={before_count}, after={after_count})"

    latest_artifact_id = contract.functions.agentArtifacts(test_agent_id, after_count - 1).call()
    artifact_onchain = contract.functions.artifacts(latest_artifact_id).call()

    # Tuple format from Solidity getter:
    # (artifactId, agentId, artifactType, dataHash, timestamp)
    onchain_hash_hex = Web3.to_hex(artifact_onchain[3])
    if onchain_hash_hex.lower() != expected_hash_hex.lower():
        return False, (
            "hash mismatch. "
            f"expected={expected_hash_hex}, onchain={onchain_hash_hex}, artifactId={latest_artifact_id}"
        )

    return True, f"on-chain hash verified (artifactId={latest_artifact_id}, tx={tx_hash})"


def step_verify_kraken_paper_cli() -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            ["wsl", "kraken", "paper", "buy", "XBTUSD", "0.001"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=45
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["wsl", "bash", "-lc", "kraken paper buy XBTUSD 0.001"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45
            )
    except FileNotFoundError:
        return False, "`wsl` command not found on Windows PATH"
    except subprocess.TimeoutExpired:
        return False, "paper trade command timed out after 45s"
    except Exception as e:
        return False, str(e)

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr if stderr else stdout if stdout else "no output"
        return False, f"paper trade command failed: {details}"

    output = (result.stdout or "").strip()
    if len(output) > 240:
        output = output[:240] + "..."

    return True, f"paper trade command succeeded. output={output or '<empty>'}"


def run_step(step_name: str, fn):
    try:
        ok, detail = fn()
        record(step_name, ok, detail)
    except Exception as e:
        record(step_name, False, f"Unhandled exception: {e}")


def main() -> int:
    os.chdir(PROJECT_ROOT)

    print("=" * 72)
    print("CHORUS Task 2 E2E Test")
    print("=" * 72)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {PROJECT_ROOT}")
    print("")

    run_step("Sub-agent vote schema/signature validation", step_validate_subagent_votes)
    run_step("Risk Sentinel veto at -3% daily PnL", step_verify_risk_veto)
    run_step("Run one full meta-agent cycle", step_run_meta_cycle)
    run_step("Decision artifact JSON created", step_verify_artifact_saved)
    run_step("Validation artifact hash logged on-chain", step_verify_hash_logged_onchain)
    run_step("Kraken paper CLI call via WSL", step_verify_kraken_paper_cli)

    print("")
    print("=" * 72)
    passed = sum(1 for status, _, _ in results if status == PASS)
    failed = sum(1 for status, _, _ in results if status == FAIL)
    total = len(results)
    print(f"Summary: {passed}/{total} PASS, {failed}/{total} FAIL")

    if failed:
        print("Failed steps:")
        for status, step, detail in results:
            if status == FAIL:
                print(f"- {step}: {detail}")
        print("=" * 72)
        return 1

    print("All Task 2 checks passed.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

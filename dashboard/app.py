import glob
import importlib
import json
import os
import sys
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from web3 import Web3

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENTS_DIR = os.path.join(PROJECT_ROOT, "agents")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")
CONTRACTS_FILE = os.path.join(PROJECT_ROOT, "contract_addresses.json")

# Always load the project-root .env regardless of current working directory.
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

AGENTS = [
    {"agent_id": 1, "agent_name": "TrendAgent", "role": "trend_follower", "metadata_uri": "ipfs://chorus/trend"},
    {"agent_id": 2, "agent_name": "ReversalAgent", "role": "mean_reversion", "metadata_uri": "ipfs://chorus/reversal"},
    {"agent_id": 3, "agent_name": "RiskSentinel", "role": "risk_sentinel", "metadata_uri": "ipfs://chorus/risk"},
    {"agent_id": 4, "agent_name": "SentimentAgent", "role": "sentiment_scanner", "metadata_uri": "ipfs://chorus/sentiment"},
]

REPUTATION_ABI = [
    {
        "inputs": [{"name": "agentId", "type": "uint256"}],
        "name": "getScore",
        "outputs": [{"name": "", "type": "int256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

IDENTITY_ABI = [
    {
        "inputs": [{"name": "", "type": "uint256"}],
        "name": "agents",
        "outputs": [
            {"name": "agentId", "type": "uint256"},
            {"name": "agentWallet", "type": "address"},
            {"name": "name", "type": "string"},
            {"name": "role", "type": "string"},
            {"name": "metadataURI", "type": "string"},
            {"name": "active", "type": "bool"},
            {"name": "registeredAt", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def _safe_read_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_contract_addresses() -> Dict[str, str]:
    data = _safe_read_json(CONTRACTS_FILE) or {}
    return {
        "identity": data.get("identity") or os.getenv("IDENTITY_CONTRACT", ""),
        "reputation": data.get("reputation") or os.getenv("REPUTATION_CONTRACT", ""),
        "validation": data.get("validation") or os.getenv("VALIDATION_CONTRACT", ""),
    }


def _get_agent_chain_clients():
    """
    Reuse the same shared web3 connection and contract map as agent scripts.
    This avoids dashboard-only connectivity drift.
    """
    try:
        import utils
        agent_w3 = utils.w3
        agent_contracts = getattr(utils, "CONTRACTS", {})

        # If utils imported before env vars were loaded, refresh it once.
        if hasattr(agent_w3, "is_connected") and not agent_w3.is_connected():
            importlib.reload(utils)
            agent_w3 = utils.w3
            agent_contracts = getattr(utils, "CONTRACTS", {})

        return agent_w3, dict(agent_contracts or {})
    except Exception as e:
        return None, {"_error": str(e)}


def _get_latest_decision() -> Optional[dict]:
    decision_files = glob.glob(os.path.join(ARTIFACTS_DIR, "decision_*.json"))
    if not decision_files:
        return None
    latest_path = max(decision_files, key=os.path.getmtime)
    data = _safe_read_json(latest_path)
    if not data:
        return None
    data["_file"] = latest_path
    data["_file_mtime"] = int(os.path.getmtime(latest_path))
    return data


def _collect_live_votes(pair: str) -> List[dict]:
    try:
        from trend_agent import analyze as trend_analyze
        from reversal_agent import analyze as reversal_analyze
        from risk_sentinel import analyze as risk_analyze
        from sentiment_agent import analyze as sentiment_analyze
    except Exception as e:
        return [{"error": f"Could not import agents: {e}"}]

    votes = []
    for fn in [trend_analyze, reversal_analyze, risk_analyze, sentiment_analyze]:
        try:
            votes.append(fn(pair))
        except Exception as e:
            votes.append({"error": str(e)})
    return votes


def _fetch_onchain_state():
    w3, agent_contracts = _get_agent_chain_clients()
    addresses = _load_contract_addresses()
    if isinstance(agent_contracts, dict):
        addresses["identity"] = agent_contracts.get("identity") or addresses["identity"]
        addresses["reputation"] = agent_contracts.get("reputation") or addresses["reputation"]
        addresses["validation"] = agent_contracts.get("validation") or addresses["validation"]

    reputation = {}
    identity = {}
    chain_status = {
        "message": "Contracts deployed on Base Sepolia — verify at sepolia.basescan.org"
    }
    if not w3:
        return reputation, identity, chain_status

    rep_contract = None
    if addresses["reputation"]:
        rep_contract = w3.eth.contract(
            address=Web3.to_checksum_address(addresses["reputation"]),
            abi=REPUTATION_ABI,
        )

    id_contract = None
    if addresses["identity"]:
        id_contract = w3.eth.contract(
            address=Web3.to_checksum_address(addresses["identity"]),
            abi=IDENTITY_ABI,
        )

    for agent in AGENTS:
        agent_id = agent["agent_id"]
        if rep_contract:
            try:
                reputation[str(agent_id)] = int(rep_contract.functions.getScore(agent_id).call())
            except Exception:
                reputation[str(agent_id)] = None
        else:
            reputation[str(agent_id)] = None

        if id_contract:
            try:
                info = id_contract.functions.agents(agent_id).call()
                identity[str(agent_id)] = {
                    "agent_id": int(info[0]),
                    "wallet": info[1],
                    "name": info[2],
                    "role": info[3],
                    "metadata_uri": info[4],
                    "active": bool(info[5]),
                    "registered_at": int(info[6]),
                    "registered": bool(info[0]) and bool(info[2]),
                }
            except Exception:
                identity[str(agent_id)] = {"registered": False}
        else:
            identity[str(agent_id)] = {"registered": False}

    return reputation, identity, chain_status


def _recent_artifacts(limit: int = 12) -> List[dict]:
    if not os.path.isdir(ARTIFACTS_DIR):
        return []

    artifact_paths = glob.glob(os.path.join(ARTIFACTS_DIR, "*.json"))
    artifact_paths.sort(key=os.path.getmtime, reverse=True)

    items = []
    for path in artifact_paths[:limit]:
        payload = _safe_read_json(path) or {}
        items.append(
            {
                "file": os.path.basename(path),
                "path": path,
                "artifact_type": payload.get("type", "UNKNOWN"),
                "timestamp": payload.get("timestamp"),
                "pair": payload.get("pair"),
                "decision": payload.get("decision", {}).get("decision") if isinstance(payload.get("decision"), dict) else None,
            }
        )
    return items


def _last_trade_decision(artifacts: List[dict]) -> Optional[dict]:
    for item in artifacts:
        if item["artifact_type"] in {"TRADE_CONFIRMED", "TRADE_INTENT"}:
            return item
    return None


def _enrich_votes(votes: List[dict], reputation: Dict[str, Optional[int]]) -> List[dict]:
    enriched = []
    for vote in votes:
        if "error" in vote:
            enriched.append(vote)
            continue
        rep = reputation.get(str(vote.get("agent_id")))
        out = dict(vote)
        out["reputation"] = 50 if rep is None else rep
        enriched.append(out)
    return enriched


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def get_state():
    try:
        latest_decision = _get_latest_decision()
        pair = "XBTUSD"
        if latest_decision and latest_decision.get("pair"):
            pair = latest_decision["pair"]

        reputation, identity, chain_status = _fetch_onchain_state()
        live_votes = _collect_live_votes(pair)
        artifact_votes = latest_decision.get("votes", []) if latest_decision else []

        votes_source = "live" if live_votes and "error" not in live_votes[0] else "artifact"
        votes = live_votes if votes_source == "live" else artifact_votes
        votes = _enrich_votes(votes, reputation)

        artifacts = _recent_artifacts()
        last_trade = _last_trade_decision(artifacts)

        state = {
            "generated_at": int(time.time()),
            "pair": pair,
            "cycle_timestamp": latest_decision.get("cycle_timestamp") if latest_decision else None,
            "decision": latest_decision.get("decision") if latest_decision else {"decision": "HOLD", "reason": "No decision artifact found yet"},
            "current_votes": votes,
            "votes_source": votes_source,
            "onchain_reputation": reputation,
            "identity_registry": identity,
            "recent_artifacts": artifacts,
            "last_trade_decision": last_trade,
            "contracts": _load_contract_addresses(),
            "chain_status": chain_status,
            "last_decision_file": latest_decision.get("_file") if latest_decision else None,
        }
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/contracts")
def get_contracts():
    return jsonify(_load_contract_addresses())


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

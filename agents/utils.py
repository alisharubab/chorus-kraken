"""
CHORUS -- Shared Utilities
Used by all sub-agents for blockchain connection, Kraken data, vote signing, and hashing.
"""
import json
import hashlib
import os
import time
import shlex
import subprocess
import urllib.parse
import requests

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------
# Blockchain Connection (Base Sepolia via Alchemy)
# ----------------------------------------------
w3 = Web3(Web3.HTTPProvider(
    f"https://base-sepolia.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"
))

# Load deployed contract addresses
CONTRACT_ADDRESSES_FILE = os.path.join(os.path.dirname(__file__), '..', 'contract_addresses.json')

def load_contracts():
    """Load contract addresses from the deployment output file."""
    try:
        with open(CONTRACT_ADDRESSES_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        print("[WARN] contract_addresses.json not found. Deploy contracts first:")
        print("   npx hardhat run scripts/deploy.js --network baseSepolia")
        return {}

CONTRACTS = load_contracts()

# ----------------------------------------------
# Market Data -- Kraken REST API (public, no auth)
# ----------------------------------------------
def _kraken_public_request(endpoint: str, params: dict):
    """
    Fetch Kraken public API JSON.
    Strategy:
      1) Try native Windows requests
      2) If that fails (DNS/proxy/network), fallback to WSL curl
    """
    base_url = "https://api.kraken.com/0/public"
    query = urllib.parse.urlencode(params or {})
    url = f"{base_url}/{endpoint}" + (f"?{query}" if query else "")

    # Attempt 1: Windows Python requests
    try:
        return requests.get(url, timeout=15).json()
    except Exception as native_error:
        # Attempt 2: WSL curl fallback
        try:
            cmd = f"curl -sS --max-time 15 {shlex.quote(url)}"
            result = subprocess.run(
                ["wsl", "bash", "-lc", cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=25,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip() or result.stdout.strip() or "unknown WSL curl error"
                print(f"Error fetching Kraken {endpoint} via WSL curl: {stderr}")
                print(f"Original Windows request error: {native_error}")
                return {}
            return json.loads(result.stdout)
        except Exception as wsl_error:
            print(f"Error fetching Kraken {endpoint}: native={native_error}; wsl={wsl_error}")
            return {}


def _first_result_key(result_obj: dict):
    """Kraken payloads may include helper keys like 'last'; choose the data key."""
    if not isinstance(result_obj, dict):
        return None
    keys = [k for k in result_obj.keys() if k != "last"]
    return keys[0] if keys else None


def get_kraken_price(pair='XBTUSD'):
    """Fetch current price from Kraken REST API (public endpoint, no API key needed)."""
    try:
        r = _kraken_public_request("Ticker", {"pair": pair})
        if r.get('error') and len(r['error']) > 0:
            print(f"Kraken API error: {r['error']}")
            return None
        key = _first_result_key(r.get("result", {}))
        if not key:
            return None
        return float(r['result'][key]['c'][0])  # Last trade price
    except Exception as e:
        print(f"Error fetching Kraken price: {e}")
        return None

def get_kraken_ohlcv(pair='XBTUSD', interval=60):
    """
    Fetch hourly OHLCV candles from Kraken (public endpoint).
    Each candle: [time, open, high, low, close, vwap, volume, count]
    """
    try:
        r = _kraken_public_request("OHLC", {"pair": pair, "interval": interval})
        if r.get('error') and len(r['error']) > 0:
            print(f"Kraken API error: {r['error']}")
            return []
        key = _first_result_key(r.get("result", {}))
        if not key:
            return []
        return r['result'][key]
    except Exception as e:
        print(f"Error fetching Kraken OHLCV: {e}")
        return []

# ----------------------------------------------
# Vote Signing (EIP-712 style)
# ----------------------------------------------
def sign_vote(vote_data: dict, private_key: str) -> str:
    """Sign a vote dict using EIP-191 personal sign and return hex signature."""
    msg = json.dumps(vote_data, sort_keys=True)
    msg_hash = encode_defunct(text=msg)
    signed = Account.sign_message(msg_hash, private_key=private_key)
    return signed.signature.hex()

# ----------------------------------------------
# Artifact Hashing
# ----------------------------------------------
def hash_artifact(artifact: dict) -> str:
    """Create a deterministic SHA-256 hash of an artifact for on-chain logging."""
    content = json.dumps(artifact, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

# ----------------------------------------------
# PRISM API (Strykr market data)
# ----------------------------------------------
def get_prism_data(endpoint='market/sentiment'):
    """
    Fetch data from PRISM API (Strykr).
    Uses PRISM_API_KEY from .env.
    """
    base_url = 'https://api.strykr.com/v1'  # Placeholder -- update with actual PRISM base URL
    headers = {
        'Authorization': f"Bearer {os.getenv('PRISM_API_KEY')}",
        'Content-Type': 'application/json'
    }
    try:
        r = requests.get(f'{base_url}/{endpoint}', headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print(f"PRISM API error: {e}")
        return {}

# ----------------------------------------------
# Kraken Balance Check (CLI -> Python fallback)
# ----------------------------------------------
def check_kraken_balance():
    """
    Check Kraken account balance.
    Tries Kraken CLI first, falls back to Python REST client.
    Returns a dict of asset -> balance, or None on error.
    """
    import subprocess

    def run_wsl_kraken(args, timeout=15):
        direct = subprocess.run(
            ['wsl', 'kraken', *args],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        if direct.returncode == 0:
            return direct
        return subprocess.run(
            ['wsl', 'bash', '-lc', ' '.join(['kraken', *args])],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )

    # Try Kraken CLI first (expected format: kraken balance -o json)
    try:
        result = run_wsl_kraken(['balance', '-o', 'json'], timeout=15)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass  # CLI not installed or failed -- fall back to Python client

    # Fallback: Python REST client
    try:
        from kraken_client import get_balance
        resp = get_balance()
        if resp.get('error') and len(resp['error']) > 0:
            print(f"  [WARN] Kraken balance check error: {resp['error']}")
            return None
        return resp.get('result', {})
    except ImportError:
        print("  [WARN] kraken_client.py not found and Kraken CLI not installed")
        return None
    except Exception as e:
        print(f"  [WARN] Kraken balance check failed: {e}")
        return None

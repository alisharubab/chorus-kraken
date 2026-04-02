"""
CHORUS -- End-to-End Test Script
Verifies every component of the system before going live.

Usage: python scripts/test_cycle.py

Tests:
  1. Blockchain connection (Base Sepolia via Alchemy)
  2. Smart contract connectivity (Identity, Reputation, Validation)
  3. Kraken API connectivity (balance check)
  4. Individual sub-agent execution
  5. Full Senate decision cycle
  6. Artifact generation verification
"""
import os
import sys
import json
import time

# Add agents/ to path so we can import everything
agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')
sys.path.insert(0, agents_dir)

project_root = os.path.join(os.path.dirname(__file__), '..')
os.chdir(project_root)

from dotenv import load_dotenv
load_dotenv()


PASS = '[OK]'
FAIL = '[FAIL]'
WARN = '[WARN]'
results = []


def test(name, func):
    """Run a test and record the result."""
    try:
        success, detail = func()
        status = PASS if success else FAIL
        results.append((status, name, detail))
        print(f'  {status} {name}: {detail}')
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f'  {FAIL} {name}: {e}')


# ----------------------------------------------
# Test 1: Environment Variables
# ----------------------------------------------
def test_env():
    missing = []
    required = ['PRIVATE_KEY', 'ALCHEMY_API_KEY', 'KRAKEN_API_KEY', 'KRAKEN_API_SECRET']
    for key in required:
        if not os.getenv(key):
            missing.append(key)
    if missing:
        return False, f'Missing: {", ".join(missing)}'

    pk = os.getenv('PRIVATE_KEY', '')
    if not pk.startswith('0x'):
        return False, 'PRIVATE_KEY missing 0x prefix'

    return True, f'All {len(required)} keys present, PRIVATE_KEY has 0x prefix'


# ----------------------------------------------
# Test 2: Blockchain Connection
# ----------------------------------------------
def test_blockchain():
    from utils import w3
    if not w3.is_connected():
        return False, 'Cannot connect to Base Sepolia via Alchemy'
    block = w3.eth.block_number
    return True, f'Connected to Base Sepolia (block #{block})'


# ----------------------------------------------
# Test 3: Contract Addresses
# ----------------------------------------------
def test_contracts():
    from utils import CONTRACTS
    required = ['identity', 'reputation', 'validation']
    for key in required:
        if not CONTRACTS.get(key):
            return False, f'Missing contract address: {key}'
    return True, f'All 3 contracts loaded: {", ".join(CONTRACTS[k][:10] + "..." for k in required)}'


# ----------------------------------------------
# Test 4: Reputation Contract Read
# ----------------------------------------------
def test_reputation_read():
    from web3 import Web3
    from utils import w3, CONTRACTS
    abi = [
        {
            'inputs': [{'name': 'agentId', 'type': 'uint256'}],
            'name': 'getScore',
            'outputs': [{'name': '', 'type': 'int256'}],
            'stateMutability': 'view',
            'type': 'function'
        }
    ]
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS['reputation']),
        abi=abi
    )
    score = contract.functions.getScore(1).call()
    return True, f'TrendAgent (ID=1) reputation score: {score}'


# ----------------------------------------------
# Test 5: Kraken Public API
# ----------------------------------------------
def test_kraken_public():
    from utils import get_kraken_price
    price = get_kraken_price('XBTUSD')
    if price is None:
        return False, 'Could not fetch BTC price'
    return True, f'BTC/USD: ${price:,.2f}'


# ----------------------------------------------
# Test 6: Kraken Private API (Balance)
# ----------------------------------------------
def test_kraken_balance():
    from kraken_client import get_balance
    resp = get_balance()
    if resp.get('error') and len(resp['error']) > 0:
        return False, f'API error: {resp["error"]}'
    balances = resp.get('result', {})
    non_zero = {k: v for k, v in balances.items() if float(v) > 0}
    if non_zero:
        bal_str = ', '.join(f'{k}={v}' for k, v in non_zero.items())
        return True, f'Balances: {bal_str}'
    return True, 'Connected (all balances zero -- OK for testing)'


# ----------------------------------------------
# Test 7: Individual Agents
# ----------------------------------------------
def test_trend_agent():
    from trend_agent import analyze
    vote = analyze('XBTUSD')
    return True, f'{vote["direction"]} {vote["confidence"]}% -- {vote.get("reason", "")}'

def test_reversal_agent():
    from reversal_agent import analyze
    vote = analyze('XBTUSD')
    return True, f'{vote["direction"]} {vote["confidence"]}% -- {vote.get("reason", "")}'

def test_risk_sentinel():
    from risk_sentinel import analyze
    vote = analyze('XBTUSD')
    return True, f'{vote["direction"]} {vote["confidence"]}% -- {vote.get("reason", "")}'

def test_sentiment_agent():
    from sentiment_agent import analyze
    vote = analyze('XBTUSD')
    return True, f'{vote["direction"]} {vote["confidence"]}% -- {vote.get("reason", "")}'


# ----------------------------------------------
# Test 8: Full Cycle (dry run)
# ----------------------------------------------
def test_full_cycle():
    from meta_agent import run_cycle
    result = run_cycle('XBTUSD')
    return True, f'Decision: {result["decision"]} -- {result["reason"]}'


# ----------------------------------------------
# Test 9: Artifacts Directory
# ----------------------------------------------
def test_artifacts():
    artifacts_dir = os.path.join(project_root, 'artifacts')
    if not os.path.exists(artifacts_dir):
        return False, 'artifacts/ directory not found'
    files = [f for f in os.listdir(artifacts_dir) if f.endswith('.json')]
    return True, f'{len(files)} artifact files in artifacts/'


# ----------------------------------------------
# Run All Tests
# ----------------------------------------------
if __name__ == '__main__':
    print('=' * 60)
    print('  CHORUS End-to-End Test Suite')
    print('=' * 60)
    print(f'  Time: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print('')

    print('[ENV] Environment:')
    test('Environment variables', test_env)
    print('')

    print('[CHAIN] Blockchain:')
    test('Base Sepolia connection', test_blockchain)
    test('Contract addresses', test_contracts)
    test('Reputation contract read', test_reputation_read)
    print('')

    print('[KRAKEN] Kraken:')
    test('Kraken public API (BTC price)', test_kraken_public)
    test('Kraken private API (balance)', test_kraken_balance)
    print('')

    print('[AGENTS] Sub-Agents:')
    test('Trend Agent', test_trend_agent)
    test('Reversal Agent', test_reversal_agent)
    test('Risk Sentinel', test_risk_sentinel)
    test('Sentiment Agent', test_sentiment_agent)
    print('')

    print('[SENATE] Full Senate Cycle:')
    test('Complete decision cycle', test_full_cycle)
    print('')

    print('[FILES] Artifacts:')
    test('Artifact storage', test_artifacts)
    print('')

    # Summary
    print('=' * 60)
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = sum(1 for s, _, _ in results if s == FAIL)
    total = len(results)
    print(f'  Results: {passed}/{total} passed, {failed} failed')

    if failed == 0:
        print('  ALL TESTS PASSED -- CHORUS is ready!')
    else:
        print(f'\n  Failed tests:')
        for status, name, detail in results:
            if status == FAIL:
                print(f'    {FAIL} {name}: {detail}')

    print('=' * 60)

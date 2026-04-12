"""
CHORUS -- Validation Artifact Logger
Logs cryptographic hashes of validation artifacts on-chain to the ValidationRegistry.

Artifact types:
  VOTE              -- Sub-agent vote
  META_DECISION     -- Meta-agent tally result
  TRADE_INTENT      -- Before sending trade to Kraken
  TRADE_CONFIRMED   -- After Kraken confirms the order
  RISK_CHECK        -- Every Risk Sentinel evaluation
  REPUTATION_UPDATE -- After reputation scores change
"""
import os
import json
import time
import sys

sys.path.insert(0, os.path.dirname(__file__))

from web3 import Web3
from eth_account import Account
from utils import w3, CONTRACTS, hash_artifact
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------
# Validation Registry ABI (minimal)
# ----------------------------------------------
VALIDATION_ABI = [
    {
        'inputs': [
            {'name': 'agentId', 'type': 'uint256'},
            {'name': 'artifactType', 'type': 'string'},
            {'name': 'dataHash', 'type': 'bytes32'}
        ],
        'name': 'logArtifact',
        'outputs': [{'name': '', 'type': 'uint256'}],
        'stateMutability': 'nonpayable',
        'type': 'function'
    }
]

# Load validation contract (only if addresses are available)
validation_contract = None
if CONTRACTS.get('validation'):
    validation_contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS['validation']),
        abi=VALIDATION_ABI
    )


def log_artifact_onchain(agent_id: int, artifact_type: str, artifact_data: dict):
    """
    Log a validation artifact both locally (JSON file) and on-chain (hash).

    Steps:
      1. Save the full artifact JSON to artifacts/ directory
      2. SHA-256 hash the artifact
      3. Submit the hash to the on-chain ValidationRegistry
      4. Wait for transaction confirmation
      5. Return the transaction hash
    """
    # 1. Save full artifact locally
    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)

    filename = os.path.join(
        artifacts_dir,
        f'{artifact_type}_{int(time.time())}_{agent_id}.json'
    )
    with open(filename, 'w') as f:
        json.dump(artifact_data, f, indent=2)
    print(f'  [SAVED] Artifact saved locally: {filename}')

    # 2. Hash the artifact
    h = hash_artifact(artifact_data)
    data_hash = bytes.fromhex(h)[:32]  # bytes32 for the contract

    # 3. Send hash on-chain
    private_key = os.getenv('PRIVATE_KEY')
    if not validation_contract:
        print('  [WARN] Validation contract not loaded -- skipping on-chain logging')
        print(f'  [HASH] Artifact hash: 0x{h}')
        return None

    if not private_key or not private_key.startswith('0x'):
        print('  [WARN] Valid PRIVATE_KEY not set -- skipping on-chain logging')
        print(f'  [HASH] Artifact hash: 0x{h}')
        return None

    try:
        account = Account.from_key(private_key)
        nonce = w3.eth.get_transaction_count(account.address)

        txn = validation_contract.functions.logArtifact(
            agent_id, artifact_type, data_hash
        ).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })

        signed = account.sign_transaction(txn)
        # web3/eth-account versions expose either raw_transaction or rawTransaction
        raw_tx = getattr(signed, 'raw_transaction', None)
        if raw_tx is None:
            raw_tx = getattr(signed, 'rawTransaction', None)
        if raw_tx is None:
            raise RuntimeError('Could not read signed raw transaction bytes')

        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f'  [OK] Artifact logged on-chain!')
        print(f'     TX: {tx_hash.hex()}')
        print(f'     Block: {receipt["blockNumber"]}')
        print(f'     Gas used: {receipt["gasUsed"]}')

        return tx_hash.hex()

    except Exception as e:
        print(f'  [FAIL] On-chain logging failed: {e}')
        print(f'  [HASH] Artifact hash (not submitted): 0x{h}')
        return None


def log_vote(agent_id: int, vote_data: dict):
    """Convenience: log a VOTE artifact."""
    return log_artifact_onchain(agent_id, 'VOTE', vote_data)


def log_decision(decision_data: dict):
    """Convenience: log a META_DECISION artifact (uses agent_id=0 for meta-agent)."""
    return log_artifact_onchain(0, 'META_DECISION', decision_data)


def log_risk_check(risk_data: dict):
    """Convenience: log a RISK_CHECK artifact."""
    return log_artifact_onchain(3, 'RISK_CHECK', risk_data)


def log_trade_intent(trade_data: dict):
    """Convenience: log a TRADE_INTENT artifact."""
    return log_artifact_onchain(0, 'TRADE_INTENT', trade_data)


def log_trade_confirmed(trade_data: dict):
    """
    Convenience: log a TRADE_CONFIRMED artifact.
    Call this AFTER Kraken CLI confirms an order.
    The trade_data should include the Kraken order response:
      - txid (Kraken transaction ID)
      - pair, volume, price, type (buy/sell)
    """
    return log_artifact_onchain(0, 'TRADE_CONFIRMED', trade_data)


def log_reputation_update(agent_id: int, update_data: dict):
    """Convenience: log a REPUTATION_UPDATE artifact."""
    return log_artifact_onchain(agent_id, 'REPUTATION_UPDATE', update_data)


if __name__ == '__main__':
    # Test: log a sample artifact
    test_artifact = {
        'type': 'TEST',
        'message': 'Testing artifact logger',
        'timestamp': int(time.time())
    }
    print('Testing artifact logger...')
    result = log_artifact_onchain(1, 'TEST', test_artifact)
    if result:
        print(f'\n[OK] Test artifact logged. TX: {result}')
    else:
        print('\n[WARN] On-chain logging skipped (see messages above)')

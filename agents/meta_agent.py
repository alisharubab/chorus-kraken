"""
CHORUS -- Meta-Agent (Committee Chair)
The decision engine that:
  1. Collects votes from all 4 sub-agents
  2. Weighs them by on-chain reputation scores
  3. Checks for Risk Sentinel veto
  4. Fires trades through Kraken paper CLI / Python REST API
  5. Logs ALL validation artifacts on-chain
"""
import os
import json
import time
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))

from web3 import Web3
from utils import w3, CONTRACTS, hash_artifact, check_kraken_balance
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------
# Contract ABIs (minimal -- just the functions we call)
# ----------------------------------------------
REPUTATION_ABI = [
    {
        'inputs': [{'name': 'agentId', 'type': 'uint256'}],
        'name': 'getScore',
        'outputs': [{'name': '', 'type': 'int256'}],
        'stateMutability': 'view',
        'type': 'function'
    }
]

# Load reputation contract (only if addresses are available)
reputation_contract = None
if CONTRACTS.get('reputation'):
    reputation_contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACTS['reputation']),
        abi=REPUTATION_ABI
    )

# ----------------------------------------------
# Configuration
# ----------------------------------------------
TRADE_THRESHOLD = 60    # Need 60% weighted signal to execute a trade
RISK_VETO_ID = 3        # Agent ID of the Risk Sentinel
TRADE_PAIR = 'XBTUSD'   # Default trading pair
TRADE_VOLUME = '0.001'  # Conservative: ~$60-90 per trade
KRAKEN_CLI_PREFIX = ['wsl', 'kraken']
TREND_AGENT_ID = 1
TREND_MOMENTUM_REQUIRED_STREAK = 3
TREND_MOMENTUM_REQUIRED_CONFIDENCE = 100
META_STATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'cache', 'meta_state.json')


def _run_wsl_kraken(args, timeout=30):
    """
    Run Kraken CLI inside WSL.
    First try direct `wsl kraken ...`, then fallback to `wsl bash -lc` for PATH-loaded shells.
    """
    direct_cmd = [*KRAKEN_CLI_PREFIX, *args]
    result = subprocess.run(
        direct_cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout
    )
    if result.returncode == 0:
        return result

    shell_cmd = ' '.join(['kraken', *args])
    fallback_cmd = ['wsl', 'bash', '-lc', shell_cmd]
    return subprocess.run(
        fallback_cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout
    )


# ----------------------------------------------
# Reputation Fetching
# ----------------------------------------------
def get_reputation_score(agent_id: int) -> int:
    """
    Fetch an agent's reputation score from the on-chain ReputationRegistry.
    Falls back to default score of 50 if contract is not available.
    """
    if reputation_contract:
        try:
            score = reputation_contract.functions.getScore(agent_id).call()
            return max(1, int(score))  # Minimum weight of 1
        except Exception as e:
            print(f"  [WARN] Could not fetch reputation for agent {agent_id}: {e}")
    return 50  # Default score


def _load_meta_state() -> dict:
    """Load persistent meta-agent state used for cross-cycle momentum tracking."""
    try:
        with open(META_STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
            if isinstance(state, dict):
                return state
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f'  [WARN] Could not read meta state file: {e}')
    return {'trend_sell_100_streak': 0, 'last_updated': 0}


def _save_meta_state(state: dict):
    """Save persistent meta-agent state to cache/ for next cycle."""
    try:
        os.makedirs(os.path.dirname(META_STATE_FILE), exist_ok=True)
        with open(META_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f'  [WARN] Could not write meta state file: {e}')


def _update_trend_sell_streak(votes: list) -> int:
    """
    Update and persist TrendAgent SELL@100 consecutive streak.
    Returns the updated streak value.
    """
    state = _load_meta_state()
    current_streak = int(state.get('trend_sell_100_streak', 0))

    trend_vote = next((v for v in votes if v.get('agent_id') == TREND_AGENT_ID), None)
    is_sell_100 = bool(
        trend_vote
        and trend_vote.get('direction') == 'SELL'
        and int(trend_vote.get('confidence', 0)) >= TREND_MOMENTUM_REQUIRED_CONFIDENCE
    )

    if is_sell_100:
        current_streak += 1
    else:
        current_streak = 0

    state['trend_sell_100_streak'] = current_streak
    state['last_updated'] = int(time.time())
    _save_meta_state(state)
    return current_streak


# ----------------------------------------------
# Vote Tally (Weighted by Reputation)
# ----------------------------------------------
def tally_votes(votes: list) -> dict:
    """
    Tally votes weighted by each agent's reputation score.
    Risk Sentinel veto overrides all other votes.
    """
    # 1. Check for Risk Sentinel veto FIRST
    for v in votes:
        if v['agent_id'] == RISK_VETO_ID and v['direction'] == 'HOLD':
            return {
                'decision': 'HOLD',
                'reason': f"VETO Risk Sentinel: {v.get('reason', 'Risk limit reached')}",
                'signal': 0,
                'vote_breakdown': {v['agent_name']: v['direction'] for v in votes}
            }

    # 2. Weighted vote tally
    buy_weight = 0
    sell_weight = 0
    total_weight = 0
    breakdown = {}

    for v in votes:
        if v['agent_id'] == RISK_VETO_ID:
            continue  # Skip risk sentinel in normal tally (it voted PROCEED)

        rep = get_reputation_score(v['agent_id'])
        weight = rep * v['confidence'] / 100
        total_weight += rep

        breakdown[v['agent_name']] = {
            'direction': v['direction'],
            'confidence': v['confidence'],
            'reputation': rep,
            'weight': round(weight, 2)
        }

        if v['direction'] == 'BUY':
            buy_weight += weight
        elif v['direction'] == 'SELL':
            sell_weight += weight

    if total_weight == 0:
        return {'decision': 'HOLD', 'reason': 'No valid votes', 'signal': 0}

    buy_pct = (buy_weight / total_weight) * 100
    sell_pct = (sell_weight / total_weight) * 100

    if buy_pct >= TRADE_THRESHOLD:
        return {
            'decision': 'BUY',
            'signal': round(buy_pct),
            'reason': f'BUY consensus: {buy_pct:.1f}% (threshold: {TRADE_THRESHOLD}%)',
            'vote_breakdown': breakdown
        }
    elif sell_pct >= TRADE_THRESHOLD:
        return {
            'decision': 'SELL',
            'signal': round(sell_pct),
            'reason': f'SELL consensus: {sell_pct:.1f}% (threshold: {TRADE_THRESHOLD}%)',
            'vote_breakdown': breakdown
        }
    else:
        return {
            'decision': 'HOLD',
            'signal': 0,
            'reason': f'No consensus. BUY:{buy_pct:.1f}% SELL:{sell_pct:.1f}% (need {TRADE_THRESHOLD}%)',
            'vote_breakdown': breakdown
        }


def apply_consecutive_trend_trigger(votes: list, base_result: dict, trend_sell_streak: int) -> dict:
    """
    Optional momentum override:
      If TrendAgent votes SELL at 100 confidence for N consecutive cycles,
      force SELL regardless of weighted consensus.
    Safety rule:
      Risk Sentinel HOLD veto still overrides this trigger.
    """
    risk_veto = any(v.get('agent_id') == RISK_VETO_ID and v.get('direction') == 'HOLD' for v in votes)
    if risk_veto:
        return base_result

    trend_vote = next((v for v in votes if v.get('agent_id') == TREND_AGENT_ID), None)
    trend_is_sell_100 = bool(
        trend_vote
        and trend_vote.get('direction') == 'SELL'
        and int(trend_vote.get('confidence', 0)) >= TREND_MOMENTUM_REQUIRED_CONFIDENCE
    )

    if trend_is_sell_100 and trend_sell_streak >= TREND_MOMENTUM_REQUIRED_STREAK:
        override = dict(base_result)
        override['decision'] = 'SELL'
        override['signal'] = 100
        override['reason'] = (
            f'MOMENTUM TRIGGER: TrendAgent SELL at {TREND_MOMENTUM_REQUIRED_CONFIDENCE}% '
            f'for {trend_sell_streak} consecutive cycles.'
        )
        override['trigger'] = {
            'type': 'CONSECUTIVE_TREND_SELL',
            'agent_id': TREND_AGENT_ID,
            'required_confidence': TREND_MOMENTUM_REQUIRED_CONFIDENCE,
            'required_streak': TREND_MOMENTUM_REQUIRED_STREAK,
            'observed_streak': trend_sell_streak,
        }
        return override

    return base_result


# ----------------------------------------------
# Trade Execution (CLI -> Python REST fallback)
# ----------------------------------------------
def execute_trade(pair, direction):
    """
    Execute a trade via Kraken.
    Strategy: Try Kraken paper CLI first, fall back to Python REST client.

    Returns the Kraken response dict on success, or a trade_intent dict on failure.
    """
    volume = TRADE_VOLUME
    order_type = 'buy' if direction == 'BUY' else 'sell'

    # --- Attempt 1: Try Kraken paper CLI ---
    try:
        result = _run_wsl_kraken(['paper', order_type, pair, volume], timeout=30)
        if result.returncode == 0:
            stdout = result.stdout.strip()
            try:
                response = json.loads(stdout) if stdout else {'raw_output': ''}
            except json.JSONDecodeError:
                response = {'raw_output': stdout}
            print(f'  [OK] Paper trade submitted via Kraken CLI')
            return _handle_trade_success(pair, direction, volume, response, 'kraken-paper-cli')
        else:
            print(f'  [WARN] Kraken CLI returned error: {result.stderr.strip()}')
    except FileNotFoundError:
        print(f'  [INFO] Kraken CLI not found on PATH -- trying Python REST client...')
    except subprocess.TimeoutExpired:
        print(f'  [WARN] Kraken CLI timed out')
    except Exception as e:
        print(f'  [WARN] Kraken CLI error: {e}')

    # --- Attempt 2: Python REST client ---
    try:
        from kraken_client import place_order
        response = place_order(pair, order_type, volume)

        if response.get('error') and len(response['error']) > 0:
            print(f'  [FAIL] Kraken API error: {response["error"]}')
            return _handle_trade_fallback(pair, direction, volume, response['error'])

        print(f'  [OK] Order placed via Kraken REST API!')
        result_data = response.get('result', {})
        if result_data.get('txid'):
            print(f'     Order ID(s): {result_data["txid"]}')
        return _handle_trade_success(pair, direction, volume, result_data, 'kraken-rest-api')

    except ImportError:
        print(f'  [FAIL] Neither Kraken CLI nor kraken_client.py available')
        return _handle_trade_fallback(pair, direction, volume, 'No Kraken client available')
    except Exception as e:
        print(f'  [FAIL] Kraken REST API error: {e}')
        return _handle_trade_fallback(pair, direction, volume, str(e))


def _handle_trade_success(pair, direction, volume, response, method):
    """Log a successful trade as a TRADE_CONFIRMED artifact."""
    from artifact_logger import log_trade_confirmed

    trade_data = {
        'type': 'TRADE_CONFIRMED',
        'pair': pair,
        'direction': direction,
        'volume': volume,
        'method': method,
        'kraken_response': response,
        'timestamp': int(time.time())
    }

    # Log on-chain
    log_trade_confirmed(trade_data)
    return trade_data


def _handle_trade_fallback(pair, direction, volume, error_info):
    """Log a failed trade attempt as a TRADE_INTENT artifact."""
    from artifact_logger import log_trade_intent

    trade_intent = {
        'type': 'TRADE_INTENT',
        'pair': pair,
        'direction': direction,
        'volume': volume,
        'kraken_configured': False,
        'error': str(error_info),
        'timestamp': int(time.time())
    }

    # Log on-chain (even failed intents are valuable audit trail)
    log_trade_intent(trade_intent)
    return trade_intent


# ----------------------------------------------
# Main Decision Cycle
# ----------------------------------------------
def run_cycle(pair='XBTUSD'):
    """
    Run one complete CHORUS decision cycle:
      1. Collect votes from all sub-agents
      2. Log each vote as on-chain artifact
      3. Tally weighted votes
      4. Log the decision as on-chain artifact
      5. Execute trade if consensus reached
      6. Save full cycle artifact locally
    """
    from artifact_logger import log_vote, log_decision, log_risk_check

    print(f'\n{"="*60}')
    print(f'  CHORUS Senate Cycle -- {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'{"="*60}')

    # Import and run each agent
    from trend_agent import analyze as trend_analyze
    from risk_sentinel import analyze as risk_analyze
    from reversal_agent import analyze as reversal_analyze
    from sentiment_agent import analyze as sentiment_analyze

    # Collect all votes
    print('\n[VOTES] Collecting votes...')
    votes = [
        trend_analyze(pair),
        reversal_analyze(pair),
        risk_analyze(pair),
        sentiment_analyze(pair),
    ]

    # Display votes and log each one on-chain
    print('\n[RESULTS] Vote Results:')
    for v in votes:
        icon = {'BUY': '[BUY]', 'SELL': '[SELL]', 'HOLD': '[HOLD]', 'PROCEED': '[OK]'}.get(v['direction'], '[--]')
        print(f'  {icon} {v["agent_name"]:20s} -> {v["direction"]:8s} ({v["confidence"]}% confidence)')
        if v.get('reason'):
            print(f'     +-- {v["reason"]}')

        # Log each sub-agent vote on-chain
        if v['agent_id'] == RISK_VETO_ID:
            log_risk_check(v)
        else:
            log_vote(v['agent_id'], v)

    # Update cross-cycle momentum state (Trend SELL@100 streak)
    trend_sell_streak = _update_trend_sell_streak(votes)
    print(f'\n[MOMENTUM] Trend SELL@100 streak: {trend_sell_streak}/{TREND_MOMENTUM_REQUIRED_STREAK}')

    # Tally votes
    print('\n[TALLY] Tallying weighted votes...')
    base_result = tally_votes(votes)
    result = apply_consecutive_trend_trigger(votes, base_result, trend_sell_streak)
    if result is not base_result and result.get('trigger', {}).get('type') == 'CONSECUTIVE_TREND_SELL':
        print('  [OVERRIDE] Consecutive Trend SELL trigger fired -> forcing SELL decision')

    decision_tag = {'BUY': '[BUY]', 'SELL': '[SELL]', 'HOLD': '[HOLD]'}.get(result['decision'], '[--]')
    print(f'\n{"-"*60}')
    print(f'  {decision_tag} DECISION: {result["decision"]} | {result["reason"]}')
    print(f'{"-"*60}')

    # Save full decision artifact locally
    artifact = {
        'type': 'META_DECISION',
        'pair': pair,
        'votes': votes,
        'decision': result,
        'meta_state': {
            'trend_sell_100_streak': trend_sell_streak
        },
        'cycle_timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'timestamp': int(time.time())
    }

    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    artifact_file = os.path.join(artifacts_dir, f'decision_{int(time.time())}.json')
    with open(artifact_file, 'w') as f:
        json.dump(artifact, f, indent=2)
    print(f'\n  [SAVED] Artifact saved: {artifact_file}')

    # Log decision on-chain
    log_decision(artifact)

    # Execute trade if BUY or SELL
    if result['decision'] in ['BUY', 'SELL']:
        print(f'\n[TRADE] Executing {result["decision"]} trade...')
        execute_trade(pair, result['decision'])
    else:
        print(f'\n  [HOLD] No trade executed')

    return result


# ----------------------------------------------
# Entry Point
# ----------------------------------------------
if __name__ == '__main__':
    import schedule

    print('CHORUS Multi-Agent Senate starting...')
    print(f'   Trading pair: {TRADE_PAIR}')
    print(f'   Cycle interval: 15 minutes')
    print(f'   Trade threshold: {TRADE_THRESHOLD}%')
    print(f'   Trade volume: {TRADE_VOLUME} BTC')
    print(f'   Risk Sentinel ID: {RISK_VETO_ID}')

    # Check Kraken balance on startup
    print('\n[BALANCE] Checking Kraken balance...')
    balance = check_kraken_balance()
    if balance is not None:
        print('  [OK] Kraken connected!')
        for asset, amount in balance.items():
            if float(amount) > 0:
                print(f'     {asset}: {amount}')
    else:
        print('  [WARN] Could not check Kraken balance -- trades may fail')

    print('')

    # Run one cycle immediately
    run_cycle(TRADE_PAIR)

    # Then schedule every 15 minutes
    schedule.every(15).minutes.do(run_cycle, pair=TRADE_PAIR)

    print('\n[SCHEDULE] Next cycle in 15 minutes. Press Ctrl+C to stop.\n')
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print('\n\n[STOP] CHORUS Senate shutting down.')

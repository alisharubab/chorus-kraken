"""
CHORUS -- Risk Sentinel (Agent ID: 3)
Strategy: Drawdown Veto
  - If daily PnL < -2.0% -> HOLD (veto all trades, 100% confidence)
  - Otherwise -> PROCEED (allow trading)
  This agent has VETO POWER -- the meta-agent always respects a Risk Sentinel HOLD.
"""
import os
import json
import time
import sys

sys.path.insert(0, os.path.dirname(__file__))

from utils import get_kraken_price, sign_vote
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = 3  # On-chain ID
AGENT_NAME = 'RiskSentinel'
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

MAX_DAILY_LOSS_PERCENT = 2.0    # Stop trading if down 2% today
MAX_POSITION_SIZE = 0.10        # Never use more than 10% of capital in one trade


def get_daily_pnl():
    """
    Read today's PnL from a local tracker file.
    In production, this would query Kraken account balance.
    """
    pnl_file = os.path.join(os.path.dirname(__file__), '..', 'daily_pnl.json')
    try:
        with open(pnl_file) as f:
            return json.load(f).get('pnl_percent', 0.0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0.0


def analyze(pair='XBTUSD') -> dict:
    """
    Check risk conditions and produce a vote.
    If daily loss limit is hit, returns HOLD with 100% confidence (veto).
    """
    daily_pnl = get_daily_pnl()

    if daily_pnl < -MAX_DAILY_LOSS_PERCENT:
        direction = 'HOLD'
        reason = f'VETO: Daily loss limit hit: {daily_pnl:.2f}% (max: -{MAX_DAILY_LOSS_PERCENT}%)'
        confidence = 100  # Absolute veto
    else:
        direction = 'PROCEED'  # Not a veto -- allows other agents' consensus
        reason = f'Risk OK. Daily PnL: {daily_pnl:.2f}%, Position limit: {MAX_POSITION_SIZE*100:.0f}%'
        confidence = 80

    vote = {
        'agent_id': AGENT_ID,
        'agent_name': AGENT_NAME,
        'pair': pair,
        'direction': direction,
        'confidence': confidence,
        'reason': reason,
        'daily_pnl': daily_pnl,
        'max_daily_loss': MAX_DAILY_LOSS_PERCENT,
        'max_position_size': MAX_POSITION_SIZE,
        'timestamp': int(time.time())
    }

    # Sign the vote
    if PRIVATE_KEY and PRIVATE_KEY.startswith('0x'):
        vote['signature'] = sign_vote(vote, PRIVATE_KEY)

    return vote


if __name__ == '__main__':
    result = analyze()
    print(json.dumps(result, indent=2))

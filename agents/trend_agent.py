"""
CHORUS -- Trend Agent (Agent ID: 1)
Strategy: Simple Moving Average (SMA) Crossover
  - SMA(10) > SMA(30) x 1.002 -> BUY
  - SMA(10) < SMA(30) x 0.998 -> SELL
  - Otherwise -> HOLD
"""
import os
import json
import time
import sys

sys.path.insert(0, os.path.dirname(__file__))

from utils import get_kraken_ohlcv, sign_vote, hash_artifact
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = 1  # On-chain ID from AgentIdentityRegistry
AGENT_NAME = 'TrendAgent'
PRIVATE_KEY = os.getenv('PRIVATE_KEY')


def compute_sma(candles, period):
    """Simple Moving Average: average of the last N closing prices."""
    if len(candles) < period:
        return None
    closes = [float(c[4]) for c in candles[-period:]]
    return sum(closes) / len(closes)


def analyze(pair='XBTUSD') -> dict:
    """
    Pull OHLCV data from Kraken, compute SMA crossover, and produce a signed vote.
    """
    candles = get_kraken_ohlcv(pair=pair, interval=60)

    if not candles or len(candles) < 30:
        vote = {
            'agent_id': AGENT_ID,
            'agent_name': AGENT_NAME,
            'pair': pair,
            'direction': 'HOLD',
            'confidence': 0,
            'reason': 'Insufficient candle data',
            'timestamp': int(time.time())
        }
        if PRIVATE_KEY and PRIVATE_KEY.startswith('0x'):
            vote['signature'] = sign_vote(vote, PRIVATE_KEY)
        return vote

    sma_10 = compute_sma(candles, 10)
    sma_30 = compute_sma(candles, 30)

    if sma_10 is None or sma_30 is None:
        direction = 'HOLD'
        confidence = 0
        reason = 'Could not compute SMAs'
    elif sma_10 > sma_30 * 1.002:
        # 10-period above 30-period by 0.2% -> bullish crossover
        direction = 'BUY'
        confidence = min(100, int((sma_10 / sma_30 - 1) * 10000))
        reason = f'Bullish crossover: SMA10={sma_10:.2f} > SMA30={sma_30:.2f}'
    elif sma_10 < sma_30 * 0.998:
        # 10-period below 30-period by 0.2% -> bearish crossover
        direction = 'SELL'
        confidence = min(100, int((1 - sma_10 / sma_30) * 10000))
        reason = f'Bearish crossover: SMA10={sma_10:.2f} < SMA30={sma_30:.2f}'
    else:
        direction = 'HOLD'
        confidence = 50
        reason = f'No clear signal: SMA10={sma_10:.2f} ~= SMA30={sma_30:.2f}'

    vote = {
        'agent_id': AGENT_ID,
        'agent_name': AGENT_NAME,
        'pair': pair,
        'direction': direction,
        'confidence': confidence,
        'reason': reason,
        'sma_10': round(sma_10, 2) if sma_10 else None,
        'sma_30': round(sma_30, 2) if sma_30 else None,
        'timestamp': int(time.time())
    }

    # Sign the vote (only if we have a real private key)
    if PRIVATE_KEY and PRIVATE_KEY.startswith('0x'):
        vote['signature'] = sign_vote(vote, PRIVATE_KEY)

    return vote


if __name__ == '__main__':
    result = analyze()
    print(json.dumps(result, indent=2))

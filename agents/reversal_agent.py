"""
CHORUS -- Reversal Agent (Agent ID: 2)
Strategy: RSI (Relative Strength Index)
  - RSI > 70 -> Overbought -> SELL
  - RSI < 30 -> Oversold -> BUY
  - Otherwise -> HOLD
"""
import os
import json
import time
import sys

sys.path.insert(0, os.path.dirname(__file__))

from utils import get_kraken_ohlcv, sign_vote
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = 2  # On-chain ID
AGENT_NAME = 'ReversalAgent'
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


def compute_rsi(candles, period=14):
    """
    Compute RSI (Relative Strength Index) from OHLCV candles.
    RSI = 100 - (100 / (1 + RS))  where RS = avg_gain / avg_loss
    """
    if len(candles) < period + 1:
        return None

    closes = [float(c[4]) for c in candles]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    # Use last (period) deltas
    recent_deltas = deltas[-(period):]
    gains = [d for d in recent_deltas if d > 0]
    losses = [-d for d in recent_deltas if d < 0]

    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0.0001  # avoid division by zero

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)


def analyze(pair='XBTUSD') -> dict:
    """
    Pull OHLCV data, compute RSI, and produce a signed vote.
    """
    candles = get_kraken_ohlcv(pair=pair, interval=60)

    if not candles or len(candles) < RSI_PERIOD + 1:
        return {
            'agent_id': AGENT_ID,
            'agent_name': AGENT_NAME,
            'pair': pair,
            'direction': 'HOLD',
            'confidence': 0,
            'reason': 'Insufficient data for RSI calculation',
            'timestamp': int(time.time())
        }

    rsi = compute_rsi(candles, RSI_PERIOD)

    if rsi is None:
        direction = 'HOLD'
        confidence = 0
        reason = 'Could not compute RSI'
    elif rsi > RSI_OVERBOUGHT:
        direction = 'SELL'
        confidence = min(100, int((rsi - RSI_OVERBOUGHT) * 3))  # Scale confidence
        reason = f'Overbought: RSI={rsi} > {RSI_OVERBOUGHT}'
    elif rsi < RSI_OVERSOLD:
        direction = 'BUY'
        confidence = min(100, int((RSI_OVERSOLD - rsi) * 3))
        reason = f'Oversold: RSI={rsi} < {RSI_OVERSOLD}'
    else:
        direction = 'HOLD'
        confidence = 50
        reason = f'Neutral: RSI={rsi} (range {RSI_OVERSOLD}-{RSI_OVERBOUGHT})'

    vote = {
        'agent_id': AGENT_ID,
        'agent_name': AGENT_NAME,
        'pair': pair,
        'direction': direction,
        'confidence': confidence,
        'reason': reason,
        'rsi': rsi,
        'timestamp': int(time.time())
    }

    if PRIVATE_KEY and PRIVATE_KEY.startswith('0x'):
        vote['signature'] = sign_vote(vote, PRIVATE_KEY)

    return vote


if __name__ == '__main__':
    result = analyze()
    print(json.dumps(result, indent=2))

"""
CHORUS -- Sentiment Agent (Agent ID: 4)
Strategy: Market-wide sentiment analysis
  - Monitors BTC volume spikes (via Kraken)
  - Optionally uses PRISM API for broader market sentiment
  - High volume + price up -> BUY
  - High volume + price down -> SELL
  - Normal volume -> HOLD
"""
import os
import json
import time
import sys

sys.path.insert(0, os.path.dirname(__file__))

from utils import get_kraken_ohlcv, get_kraken_price, sign_vote
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = 4  # On-chain ID
AGENT_NAME = 'SentimentAgent'
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

VOLUME_SPIKE_THRESHOLD = 1.5  # Volume must be 1.5x higher than the 20-period average


def compute_volume_sentiment(candles):
    """
    Analyze volume patterns to detect sentiment shifts.
    A volume spike combined with price direction gives market sentiment.
    """
    if len(candles) < 21:
        return None, None, None

    # candle format: [time, open, high, low, close, vwap, volume, count]
    volumes = [float(c[6]) for c in candles]
    closes = [float(c[4]) for c in candles]

    # Average volume over last 20 candles (excluding the latest)
    avg_volume = sum(volumes[-21:-1]) / 20
    current_volume = volumes[-1]

    # Price change over last 3 candles
    price_change_pct = ((closes[-1] - closes[-4]) / closes[-4]) * 100 if closes[-4] > 0 else 0

    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

    return volume_ratio, price_change_pct, avg_volume


def analyze(pair='XBTUSD') -> dict:
    """
    Analyze market sentiment using volume patterns and price momentum.
    """
    candles = get_kraken_ohlcv(pair=pair, interval=60)

    if not candles or len(candles) < 21:
        vote = {
            'agent_id': AGENT_ID,
            'agent_name': AGENT_NAME,
            'pair': pair,
            'direction': 'HOLD',
            'confidence': 0,
            'reason': 'Insufficient data for sentiment analysis',
            'timestamp': int(time.time())
        }
        if PRIVATE_KEY and PRIVATE_KEY.startswith('0x'):
            vote['signature'] = sign_vote(vote, PRIVATE_KEY)
        return vote

    volume_ratio, price_change, avg_vol = compute_volume_sentiment(candles)

    if volume_ratio is None:
        direction = 'HOLD'
        confidence = 0
        reason = 'Could not compute volume sentiment'
    elif volume_ratio > VOLUME_SPIKE_THRESHOLD and price_change > 0.5:
        # Volume spike + price going up -> bullish sentiment
        direction = 'BUY'
        confidence = min(100, int(volume_ratio * 20 + price_change * 10))
        reason = f'Bullish volume spike: {volume_ratio:.1f}x avg, price +{price_change:.2f}%'
    elif volume_ratio > VOLUME_SPIKE_THRESHOLD and price_change < -0.5:
        # Volume spike + price going down -> bearish sentiment
        direction = 'SELL'
        confidence = min(100, int(volume_ratio * 20 + abs(price_change) * 10))
        reason = f'Bearish volume spike: {volume_ratio:.1f}x avg, price {price_change:.2f}%'
    else:
        direction = 'HOLD'
        confidence = 50
        reason = f'Neutral: volume {volume_ratio:.1f}x avg, price {price_change:+.2f}%'

    vote = {
        'agent_id': AGENT_ID,
        'agent_name': AGENT_NAME,
        'pair': pair,
        'direction': direction,
        'confidence': confidence,
        'reason': reason,
        'volume_ratio': round(volume_ratio, 2) if volume_ratio else None,
        'price_change_pct': round(price_change, 2) if price_change else None,
        'timestamp': int(time.time())
    }

    if PRIVATE_KEY and PRIVATE_KEY.startswith('0x'):
        vote['signature'] = sign_vote(vote, PRIVATE_KEY)

    return vote


if __name__ == '__main__':
    result = analyze()
    print(json.dumps(result, indent=2))

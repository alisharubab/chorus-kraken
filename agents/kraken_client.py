"""
CHORUS -- Kraken REST API Client
Pure-Python Kraken trading client using REST API + HMAC-SHA512 authentication.
This is the fallback when Kraken CLI is unavailable.

Supports:
  - Account balance
  - Place market orders (buy/sell)
  - Query open orders
  - Query trade history

Uses KRAKEN_API_KEY and KRAKEN_API_SECRET from .env.
"""
import os
import sys
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import subprocess

import requests
from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------------
# Kraken API Configuration
# ----------------------------------------------
KRAKEN_API_URL = 'https://api.kraken.com'
API_KEY = os.getenv('KRAKEN_API_KEY', '')
API_SECRET = os.getenv('KRAKEN_API_SECRET', '')
KRAKEN_CLI_PREFIX = ['wsl', 'kraken']


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


def cli_balance() -> dict:
    """
    Run Kraken CLI balance command using the installed CLI format.
    Command: kraken balance -o json
    """
    try:
        result = _run_wsl_kraken(['balance', '-o', 'json'], timeout=20)
        if result.returncode != 0:
            return {'error': [result.stderr.strip() or result.stdout.strip() or 'Kraken CLI balance failed']}
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except FileNotFoundError:
        return {'error': ['Kraken CLI not found on PATH']}
    except subprocess.TimeoutExpired:
        return {'error': ['Kraken CLI balance command timed out']}
    except json.JSONDecodeError as e:
        return {'error': [f'Invalid JSON from Kraken CLI balance: {e}']}
    except Exception as e:
        return {'error': [str(e)]}


def cli_paper_order(direction: str, pair: str, volume: str) -> dict:
    """
    Run Kraken paper trade command using the installed CLI format.
    Example: kraken paper buy XBTUSD 0.001
    """
    side = direction.lower()
    if side not in ['buy', 'sell']:
        return {'error': [f'Invalid direction: {direction}']}

    try:
        result = _run_wsl_kraken(['paper', side, pair, str(volume)], timeout=30)
        if result.returncode != 0:
            return {'error': [result.stderr.strip() or result.stdout.strip() or 'Kraken CLI paper order failed']}

        stdout = result.stdout.strip()
        try:
            return json.loads(stdout) if stdout else {'result': 'ok', 'raw_output': ''}
        except json.JSONDecodeError:
            return {'result': 'ok', 'raw_output': stdout}
    except FileNotFoundError:
        return {'error': ['Kraken CLI not found on PATH']}
    except subprocess.TimeoutExpired:
        return {'error': ['Kraken CLI paper command timed out']}
    except Exception as e:
        return {'error': [str(e)]}


def _kraken_signature(urlpath: str, data: dict, secret: str) -> str:
    """
    Create Kraken API signature using HMAC-SHA512.
    See: https://docs.kraken.com/rest/#section/Authentication
    """
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()


def _private_request(endpoint: str, data: dict = None) -> dict:
    """
    Make an authenticated (private) request to Kraken API.
    """
    if not API_KEY or not API_SECRET:
        return {'error': ['KRAKEN_API_KEY or KRAKEN_API_SECRET not set in .env']}

    if data is None:
        data = {}

    urlpath = f'/0/private/{endpoint}'
    data['nonce'] = str(int(time.time() * 1000))

    headers = {
        'API-Key': API_KEY,
        'API-Sign': _kraken_signature(urlpath, data, API_SECRET),
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
    }

    try:
        response = requests.post(
            f'{KRAKEN_API_URL}{urlpath}',
            headers=headers,
            data=urllib.parse.urlencode(data),
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {'error': [str(e)]}


def _public_request(endpoint: str, params: dict = None) -> dict:
    """Make a public (no auth) request to Kraken API."""
    try:
        response = requests.get(
            f'{KRAKEN_API_URL}/0/public/{endpoint}',
            params=params or {},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {'error': [str(e)]}


# ----------------------------------------------
# Public Endpoints
# ----------------------------------------------
def get_ticker(pair='XBTUSD') -> dict:
    """Get current ticker data for a trading pair."""
    return _public_request('Ticker', {'pair': pair})


def get_server_time() -> dict:
    """Get Kraken server time (useful for connection test)."""
    return _public_request('Time')


# ----------------------------------------------
# Private Endpoints (Authenticated)
# ----------------------------------------------
def get_balance() -> dict:
    """
    Get account balance.
    Returns: {'error': [], 'result': {'XXBT': '0.0123', 'ZUSD': '100.00', ...}}
    """
    return _private_request('Balance')


def get_trade_balance(asset='ZUSD') -> dict:
    """Get trade balance (equity, margin, etc.)."""
    return _private_request('TradeBalance', {'asset': asset})


def place_order(pair: str, direction: str, volume: str, ordertype: str = 'market') -> dict:
    """
    Place a market order on Kraken.

    Args:
        pair: Trading pair e.g. 'XBTUSD'
        direction: 'buy' or 'sell'
        volume: Amount to trade e.g. '0.001'
        ordertype: 'market' or 'limit'

    Returns: Kraken API response with txid on success
    """
    data = {
        'pair': pair,
        'type': direction.lower(),
        'ordertype': ordertype,
        'volume': volume,
    }
    return _private_request('AddOrder', data)


def get_open_orders() -> dict:
    """Get all open orders."""
    return _private_request('OpenOrders')


def get_closed_orders() -> dict:
    """Get recent closed orders."""
    return _private_request('ClosedOrders')


def cancel_order(txid: str) -> dict:
    """Cancel an open order by transaction ID."""
    return _private_request('CancelOrder', {'txid': txid})


def get_trades_history() -> dict:
    """Get trade history."""
    return _private_request('TradesHistory')


# ----------------------------------------------
# Self-Test
# ----------------------------------------------
if __name__ == '__main__':
    print('Testing Kraken API connection...\n')

    # 1. Public: Server time
    st = get_server_time()
    if st.get('error') and len(st['error']) > 0:
        print(f'[FAIL] Server time check failed: {st["error"]}')
    else:
        print(f'[OK] Kraken server time: {st["result"]["rfc1123"]}')

    # 2. Public: BTC price
    ticker = get_ticker('XBTUSD')
    if ticker.get('error') and len(ticker['error']) > 0:
        print(f'[FAIL] Ticker check failed: {ticker["error"]}')
    else:
        key = list(ticker['result'].keys())[0]
        price = ticker['result'][key]['c'][0]
        print(f'[OK] BTC/USD price: ${float(price):,.2f}')

    # 3. Private: Account balance
    print('\n[CHECK] Checking account balance (requires valid API key)...')
    bal = get_balance()
    if bal.get('error') and len(bal['error']) > 0:
        print(f'[FAIL] Balance check failed: {bal["error"]}')
        print('   Make sure KRAKEN_API_KEY and KRAKEN_API_SECRET are correct in .env')
    else:
        result = bal.get('result', {})
        if result:
            print('[OK] Account balances:')
            for asset, amount in result.items():
                if float(amount) > 0:
                    print(f'   {asset}: {amount}')
            if not any(float(v) > 0 for v in result.values()):
                print('   (all balances are zero -- this is fine for testing)')
        else:
            print('[OK] Balance query succeeded (empty account)')

    print('\n[DONE] Kraken client test complete!')

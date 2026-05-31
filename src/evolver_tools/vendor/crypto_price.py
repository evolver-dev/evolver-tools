#!/usr/bin/env python3
"""
Cryptocurrency price ticker using CoinGecko free API.

Fetches real-time cryptocurrency prices in a specified fiat currency.
Uses only Python stdlib (urllib, json, sys) — zero external dependencies.

Usage:
    python -m evolver_tools.vendor.crypto_price --coin bitcoin
    python -m evolver_tools.vendor.crypto_price --coin ethereum --currency eur
    python -m evolver_tools.vendor.crypto_price --list
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

TOOL_META = {
    'name': 'crypto-price',
    'func': 'main',
    'desc': 'Cryptocurrency price ticker (CoinGecko)',
}

COINGECKO_SIMPLE_URL = 'https://api.coingecko.com/api/v3/simple/price'
COINGECKO_LIST_URL = 'https://api.coingecko.com/api/v3/coins/list'


def _api_get(url: str) -> dict:
    """Make a GET request to the CoinGecko API and return parsed JSON."""
    req = urllib.request.Request(url, headers={'User-Agent': 'crypto-price/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', errors='replace') if e.fp else ''
        print(f'HTTP error {e.code}: {msg}', file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f'Network error: {e.reason}', file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, OSError, ValueError) as e:
        print(f'Error parsing response: {e}', file=sys.stderr)
        sys.exit(1)


def list_coins() -> None:
    """Fetch and display all available coins from CoinGecko."""
    data = _api_get(COINGECKO_LIST_URL)
    print(f'Total coins listed: {len(data)}\n')
    # Show first 50 as a sample; user can filter with grep
    for coin in data[:50]:
        print(f'{coin["id"]:40s}  {coin["symbol"]:10s}  {coin["name"]}')
    if len(data) > 50:
        print(f'\n... and {len(data) - 50} more. Pipe through grep or use --coin <id>.')


def get_price(coin: str, currency: str) -> None:
    """Fetch and display the price for a single coin."""
    url = f'{COINGECKO_SIMPLE_URL}?ids={coin}&vs_currencies={currency}'
    data = _api_get(url)
    if coin not in data:
        print(
            f'Coin "{coin}" not found. Use --list to see available coins.',
            file=sys.stderr,
        )
        sys.exit(1)
    if currency not in data[coin]:
        print(
            f'Currency "{currency}" not available for {coin}.',
            file=sys.stderr,
        )
        sys.exit(1)
    price = data[coin][currency]
    print(f'{coin}: {price:.8f} {currency.upper()}')


def main() -> None:
    """Parse arguments and run the appropriate action."""
    parser = argparse.ArgumentParser(
        description='Cryptocurrency price ticker (CoinGecko)',
    )
    parser.add_argument(
        '--coin',
        default='bitcoin',
        help='Coin ID to look up (default: bitcoin)',
    )
    parser.add_argument(
        '--currency',
        default='usd',
        help='Fiat currency symbol (default: usd)',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available coins and exit',
    )
    args = parser.parse_args()

    if args.list:
        list_coins()
    else:
        get_price(args.coin, args.currency)


if __name__ == '__main__':
    main()

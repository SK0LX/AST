"""
Listens for new Pump.fun token creations via PumpPortal WebSocket.
"""

import asyncio
import json
from datetime import datetime
from pprint import pprint

import websockets

# PumpPortal WebSocket URL
WS_URL = "wss://pumpportal.fun/api/data"


def format_sol(value):
    return f"{value:.6f} SOL"


def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")


async def listen_for_new_tokens(ctx):
    ws = ctx.ws

    await ws.send(json.dumps({"method": "subscribeNewToken", "params": []}))
    print("Listening for new token creations...")

    while True:
        try:
            message = await ws.recv()
            data = json.loads(message)

            if "method" in data and data["method"] == "newToken":
                token_info = data.get("params", [{}])[0]
            elif "signature" in data and "mint" in data:
                token_info = data
            else:
                continue

            virtual_sol = token_info.get('vSolInBondingCurve', 0)
            virtual_tokens = token_info.get('vTokensInBondingCurve', 0)
            price = ((virtual_sol) / (virtual_tokens))
            print(price)

            token_data = {
                "name": token_info.get('name'),
                "symbol": token_info.get('symbol'),
                "address": token_info.get('mint'),
                "creator": token_info.get('traderPublicKey'),
                "sol_amount": token_info.get('solAmount'),
                "initial_buy": format_sol(token_info.get('initialBuy', 0)),
                "market_cap": format_sol(token_info.get('marketCapSol', 0)),
                "bonding_curve": token_info.get('bondingCurveKey'),
                "virtual_sol": format_sol(virtual_sol),
                "virtual_tokens": f"{virtual_tokens:,.0f}",
                "metadata_uri": token_info.get('uri'),
                "signature": token_info.get('signature'),
                "price": price
            }
            pprint(token_info)

            yield token_data

        except websockets.exceptions.ConnectionClosed:
            print("\nWebSocket connection closed. Reconnecting...")
            break
        except json.JSONDecodeError:
            print(f"\nReceived non-JSON message: {message}")
        except Exception as e:
            print(f"\nAn error occurred: {e}")


async def main():
    while True:
        try:
            async for token in listen_for_new_tokens():
                print("\n" + "=" * 50)
                print(f"New token created: {token['name']} ({token['symbol']})")
                print("=" * 50)
                for key, value in token.items():
                    print(f"{key.replace('_', ' ').title():<15}: {value}")
                print("=" * 50)
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

async def main():
    while True:
        try:
            async for token in listen_for_new_tokens():
                print("\n" + "=" * 50)
                print(f"New token created: {token['name']} ({token['symbol']})")
                print("=" * 50)
                for key, value in token.items():
                    print(f"{key.replace('_', ' ').title():<15}: {value}")
                print("=" * 50)
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())


async def main():
    while True:
        try:
            await listen_for_new_tokens()
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
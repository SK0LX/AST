import asyncio
import json
import base64
import struct
import websockets
import os
import time
import requests
from typing import *
from datetime import datetime

from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from construct import Struct, Int64ul, Flag
from solana.rpc.async_api import AsyncClient

from config import *
from coin_data import get_coin_data, sol_for_tokens, tokens_for_sol
from pump_fun import buy, sell

from listen_blocksubscribe import listen_for_new_tokens
from get_bonding_curve_status import get_curve_progress

from context import AppContext

ctx = AppContext()


async def execute_trade(mint, bonding_curve, ctx):
    delay1, delay2 = 1,2
    await asyncio.sleep(delay1)

    try:
        buy_price = await get_curve_progress("7Z6ZMbwht1CwWYMYAespazVeqny3jcBJSR3c39uTjiTX", ctx)
        print(buy_price)
    except ValueError as e:
        print(f"Skipping trade for {mint} due to {e}")
        return

    print(f"Emulating buy for {mint} with {1234:.6f} SOL")
    exit(0)

    start_price = buy_price

    tp_price = buy_price * TAKE_PROFIT
    sl_price = buy_price * STOP_LOSS
    buy(payer_keypair, mint, bonding_curve, associated_bonding_curve, BUY_AMOUNT, 5)
    print(f"Bought at {buy_price}. Target TP: {tp_price}, SL: {sl_price}")
    start_time = time.time()

    while True:
        await asyncio.sleep(5)
        try:
            current_price = get_token_price(bonding_curve)
        except ValueError as e:
            print(f"Error fetching current price for {mint}: {e}")
            continue

        print(f"Current price: {current_price}")

        if current_price >= tp_price:
            print(f"\033[92mTP reached! Selling at {current_price}\033[0m")
            profit = position_size * (current_price / buy_price - 1)
            price_diff = (current_price - start_price) / start_price
            return

        if current_price <= sl_price:
            print(f"\033[91mSL reached! Selling at {current_price}\033[0m")
            loss = position_size * (current_price / buy_price - 1)
            price_diff = (current_price - start_price) / start_price
            return

        if time.time() - start_time >= delay2:
            print(f"\033[93mTimeout reached! Selling at {current_price}\033[0m")
            profit_loss = position_size * (current_price / buy_price - 1)
            price_diff = (current_price - start_price) / start_price
            return

async def trade():
    # print(f"Starting trade cycle for user {user_id}, wallet {public_key[:8]}")
    await ctx.init()
    async for args in listen_for_new_tokens(ctx):
        mint = args['address']
        bonding_curve = args['bonding_curve']
        
        print(f"New token detected: {mint}, bonding curve: {bonding_curve}")
          # Новый клиент для каждой итерации
        await execute_trade(mint, bonding_curve, ctx)


if __name__ == "__main__":
    asyncio.run(trade())
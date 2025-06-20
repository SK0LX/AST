import asyncio
import json
import base64
import struct
import websockets
import os
import time
import requests
from datetime import datetime
import numpy as np

from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from construct import Struct, Int64ul, Flag
from solana.rpc.async_api import AsyncClient
from catboost import CatBoostClassifier


from config import *
from coin_data import get_coin_data, sol_for_tokens, tokens_for_sol
from pump_fun import buy, sell

from listen_blocksubscribe import listen_for_new_tokens
from get_bonding_curve_status import get_curve_progress

from context import AppContext

ctx = AppContext()

EXPECTED_DISCRIMINATOR = struct.pack("<Q", 6966180631402821399)
TOKEN_DECIMALS = 6
WEBSOCKET_TIMEOUT = 60
RECONNECT_DELAY = 5
CURVE_STATE_RETRIES = 5
CURVE_STATE_DELAY = 3

TAKE_PROFIT = 1.5 
STOP_LOSS = 0.8   

FILENAME = "trades_backup.json"

RPC_URL = "https://api.mainnet-beta.solana.com"

model = CatBoostClassifier()
model.load_model("catboost_model_balanced.cbm")


def round_float(value, decimals=10):
    return round(value, decimals)

import json
import os

FILENAME = "backup.json"  # Укажи имя файла, если оно ещё не определено
balance = 100.0

def load_backup():
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            return json.load(f)
    return []  # Возвращаем пустой список вместо словаря

def save_backup(data):
    with open(FILENAME, "w") as f:
        json.dump(data, f, indent=4)

def record_trade(data, args, buy_delay, sell_delay, result):
    # Формируем запись трейда
    trade = {
        'buy_delay': buy_delay,
        'sell_delay': sell_delay,
        'initial_buy': args['initial_buy'],
        'market_cap': args['market_cap'],
        'price': args['price'],
        'sol_amount': args['sol_amount'],
        'result': result
    }
    # Добавляем трейд в список
    data.append(trade)
    # Сохраняем бэкап
    save_backup(data)

def update_balance(change):
    global balance
    balance += change
    color = "\033[92m" if change > 0 else "\033[91m"
    print(f"{color}Balance change: {change:.6f} SOL | New balance: {balance:.6f} SOL\033[0m")

def generate_times():
    buy_delay = 0
    sell_delay = 25
    return buy_delay, sell_delay

def clean_data(args):
    # Очистка числовых данных
    initial_buy = float(args['initial_buy'].replace(' SOL', '')) if 'SOL' in str(args['initial_buy']) else float(args['initial_buy'])
    market_cap = float(args['market_cap'].replace(' SOL', '')) if 'SOL' in str(args['market_cap']) else float(args['market_cap'])
    price = float(args['price'])  # Здесь предполагается, что цена уже в нужном формате
    sol_amount = float(args['sol_amount'])  # Аналогично

    # Возвращаем очищенные данные в формате, который принимает модель
    return np.array([[initial_buy, market_cap, price, sol_amount]])

async def execute_trade(payer_keypair, args, mint, bonding_curve, position_size, trade_history):
    delay1, delay2 = generate_times()
    await asyncio.sleep(0.1)
    start_time = time.time()

    try:
        buy_price = args["price"]
        if not "pump" in mint:
            return
        print(buy_price)
    except ValueError as e:
        print(f"Skipping trade for {mint} due to {e}")
        return
    
    start_time = time.time()
    while True:
        await asyncio.sleep(0.5)
        try:
            buy_price = await get_curve_progress(mint, ctx)
            break
        except ValueError as e:
            print(f"Error fetching current price for {mint}: {e}")
            continue


    if (time.time() - start_time) > 2:
        return
    print(f"Emulating buy for {mint} with {position_size:.6f} SOL")
    start_price = buy_price

    tp_price = buy_price * TAKE_PROFIT
    sl_price = buy_price * STOP_LOSS
    ####
    time.sleep(0)

    print(f"Bought at {buy_price}. Target TP: {tp_price}, SL: {sl_price}")
    start_time = time.time()

    while True:
        await asyncio.sleep(1)
        try:
            current_price = await get_curve_progress(mint, ctx)
        except ValueError as e:
            print(f"Error fetching current price for {mint}: {e}")
            continue

        print(f"Current price: {current_price}")

        if current_price >= tp_price:
            print(f"\033[92mTP reached! Selling at {current_price}\033[0m")
            ###
            profit = position_size * (current_price / buy_price - 1)
            update_balance(profit)
            price_diff = (current_price - start_price) / start_price
            #record_trade(trade_history, args, delay1, delay2, price_diff)
            return

        if current_price <= sl_price:
            print(f"\033[91mSL reached! Selling at {current_price}\033[0m")
            ###
            loss = position_size * (current_price / buy_price - 1)
            update_balance(loss)
            price_diff = (current_price - start_price) / start_price
            #record_trade(trade_history, args, delay1, delay2, price_diff)
            return

        if time.time() - start_time >= delay2:
            print(f"\033[93mTimeout reached! Selling at {current_price}\033[0m")
            ###
            profit_loss = position_size * (current_price / buy_price - 1)
            update_balance(profit_loss)
            price_diff = (current_price - start_price) / start_price
            #record_trade(trade_history, args, delay1, delay2, price_diff)
            return
        

async def trade(user_id, public_key, payer_keypair, position_size, slippage_tolerance, trade_history):
    await ctx.init()

    print(f"Starting trade cycle for user {user_id}, wallet {public_key[:8]}")
    async for args in listen_for_new_tokens(ctx):
        mint = args['address']
        bonding_curve = args['bonding_curve']
        print(f"New token detected: {mint}, bonding curve: {bonding_curve}")
        
        # Преобразуем данные в формат, который принимает модель
        token_data = token_data = clean_data(args)
        print(token_data)
        
        # Получаем предсказание от модели
        prediction = model.predict(token_data)[0]
        
        if prediction == 1:
            position_size = balance * 0.25

            print(f"Token {mint} is predicted as profitable. Proceeding with trade.")
            # Новый клиент для каждой итерации
            await execute_trade(payer_keypair, args, mint, bonding_curve, position_size, trade_history)
        else:
            print(f"Token {mint} is predicted as not profitable. Skipping trade.")
        
        print("----------------------------------------------------------------------------")
        time.sleep(10)


if __name__ == "__main__":
    trade_history = load_backup()
    initial_balance = 100.0
    asyncio.run(trade("id", "pub", payer_keypair, initial_balance, 5, trade_history))
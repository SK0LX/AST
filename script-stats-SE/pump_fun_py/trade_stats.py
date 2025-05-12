import asyncio
import json
import base64
import struct
import websockets
import os
import time
import random
import os
from datetime import datetime

from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

from config import *
from pump_fun import buy, sell

import requests
import struct
import base64
import json
from construct import Struct, Int64ul, Flag
 

EXPECTED_DISCRIMINATOR = struct.pack("<Q", 6966180631402821399)
TOKEN_DECIMALS = 6
LAMPORTS_PER_SOL = 1_000_000_000
PRICE_THRESHOLD_MIN = 3.33e-08  # Пороговая цена
PRICE_THRESHOLD_MAX = 4.5e-08

# Таймаут на получение данных от WebSocket
WEBSOCKET_TIMEOUT = 30
RECONNECT_DELAY = 5

TAKE_PROFIT = 1.24  # +24%
STOP_LOSS = 0.92     # -8%

balance = 1  # 1 SOL






FILENAME = "trades_backup.json"

def round_float(value, decimals=10):
    """Округляет число с плавающей точкой до указанного количества знаков."""
    return round(value, decimals)

def load_backup():
    """Загружает историю сделок из файла, если он существует."""
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            return json.load(f)
    return {}

def save_backup(data):
    """Сохраняет историю сделок в файл."""
    with open(FILENAME, "w") as f:
        json.dump(data, f, indent=4)

def record_trade(data, min_price, max_price, buy_delay, sell_delay, result):
    """Записывает результат сделки в историю."""
    key = (
        round_float(min_price), 
        round_float(max_price), 
        buy_delay, 
        sell_delay
    )
    key_str = str(key)  # JSON не поддерживает кортежи как ключи
    
    if key_str not in data:
        data[key_str] = []

    data[key_str].append(result)
    save_backup(data)



trade_history = load_backup()


def generate_times():
    buy_delay_values = list(range(10, 61, 15))
    sell_delay_values = list(range(10, 61, 15))

    buy_delay = random.choice(buy_delay_values)
    sell_delay = random.choice(sell_delay_values)

    buy_delay = 10
    sell_delay = 20

    return  buy_delay, sell_delay

def generate_price(price):
    step = 0.1e-08
    min_price = (price // step) * step
    max_price = min_price + 0.1e-08

    return min_price, max_price



class BondingCurveState:
    _STRUCT = Struct(
        "virtual_token_reserves" / Int64ul,
        "virtual_sol_reserves" / Int64ul,
        "real_token_reserves" / Int64ul,
        "real_sol_reserves" / Int64ul,
        "token_total_supply" / Int64ul,
        "complete" / Flag
    )

    def __init__(self, data: bytes) -> None:
        parsed = self._STRUCT.parse(data[8:])
        self.__dict__.update(parsed)


# Инициализация баланса

def update_balance(change):
    global balance
    balance += change
    balance -= abs(change) * 0.01
    balance -= 0.000105
    color = "\033[92m" if change > 0 else "\033[91m"
    print(f"{color}Current balance: {balance:.4f} SOL\033[0m")


def get_pump_curve_state(curve_address: str) -> BondingCurveState:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [str(curve_address), {"encoding": "base64"}]
    }

    for attempt in range(3):  # Делаем до 3 попыток запроса
        response = requests.post(RPC, json=payload).json()
        value = response.get("result", {}).get("value")

        if value and "data" in value and value["data"]:
            data_b64 = value["data"][0]
            data = base64.b64decode(data_b64)

            if data[:8] != EXPECTED_DISCRIMINATOR:
                raise ValueError("Invalid curve state discriminator")

            return BondingCurveState(data)

        print(f"Warning: No data for bonding curve {curve_address}, attempt {attempt + 1}/3")
        time.sleep(2)  # Ждем перед повторной попыткой

    raise ValueError(f"Failed to get valid bonding curve data for {curve_address}")

def get_token_price(curve_address: str) -> float:
    curve_state = get_pump_curve_state(curve_address)
    if curve_state.virtual_token_reserves <= 0 or curve_state.virtual_sol_reserves <= 0:
        raise ValueError("Invalid reserve state")

    return (curve_state.virtual_sol_reserves / LAMPORTS_PER_SOL) / (curve_state.virtual_token_reserves / 10 ** TOKEN_DECIMALS)

def load_idl(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def decode_create_instruction(ix_data, ix_def, accounts):
    args = {}
    offset = 8  # Skip 8-byte discriminator

    for arg in ix_def['args']:
        if arg['type'] == 'string':
            length = struct.unpack_from('<I', ix_data, offset)[0]
            offset += 4
            value = ix_data[offset:offset+length].decode('utf-8')
            offset += length
        elif arg['type'] == 'publicKey':
            value = base64.b64encode(ix_data[offset:offset+32]).decode('utf-8')
            offset += 32
        else:
            raise ValueError(f"Unsupported type: {arg['type']}")
        
        args[arg['name']] = value

    # Add accounts
    args['mint'] = str(accounts[0])
    args['bondingCurve'] = str(accounts[2])
    args['associatedBondingCurve'] = str(accounts[3])
    args['user'] = str(accounts[7])

    return args




async def listen_for_create_transaction(websocket):
    idl = load_idl('pump_fun_idl.json')
    subscription_message = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "blockSubscribe",
        "params": [
            {"mentionsAccountOrProgram": str(PUMP_PROGRAM)},
            {
                "commitment": "confirmed",
                "encoding": "base64",
                "showRewards": False,
                "transactionDetails": "full",
                "maxSupportedTransactionVersion": 0
            }
        ]
    })
    await websocket.send(subscription_message)
    print(f"Subscribed to blocks mentioning program: {PUMP_PROGRAM}")

    while True:
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=WEBSOCKET_TIMEOUT)
            data = json.loads(response)

            if 'method' in data and data['method'] == 'blockNotification':
                block = data['params']['result']['value']['block']
                for tx in block.get('transactions', []):
                    tx_data_decoded = base64.b64decode(tx['transaction'][0])
                    transaction = VersionedTransaction.from_bytes(tx_data_decoded)

                    for ix in transaction.message.instructions:
                        if str(transaction.message.account_keys[ix.program_id_index]) == str(PUMP_PROGRAM):
                            ix_data = bytes(ix.data)
                            discriminator = struct.unpack('<Q', ix_data[:8])[0]

                            if discriminator == 8576854823835016728:
                                create_ix = next(instr for instr in idl['instructions'] if instr['name'] == 'create')
                                account_keys = [str(transaction.message.account_keys[index]) for index in ix.accounts]
                                decoded_args = decode_create_instruction(ix_data, create_ix, account_keys)

                                return decoded_args

        except asyncio.TimeoutError:
            print("WebSocket timeout, reconnecting...")
            break  # Разрыв цикла, чтобы переподключиться
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed: {e}. Reconnecting...")
            break  # Разрыв цикла для переподключения

async def trade():
    global balance

    while True:
        try:
            async with websockets.connect(WSS_ENDPOINT, ping_interval=20, ping_timeout=10) as websocket:
                while True:
                    print("Waiting for a new token creation...")
                    try:
                        args = await listen_for_create_transaction(websocket)
                        print(f"New token created: {args}")

                        if not args:
                            continue

                        mint = args['mint']
                        bonding_curve = args['bondingCurve']
                        associated_bonding_curve = args['associatedBondingCurve']

                        if not mint:
                            print("No valid mint found, skipping...")
                            continue

                        delay1, delay2 = generate_times()
                        print(delay1, delay2)

                        print(f"Waiting {delay1} seconds before checking the price...")
                        await asyncio.sleep(delay1)


                        
                        
                        

                        #print(f"\033[92mPrice {price} is above threshold, buying token!\033[0m")

                        mint_pubkey = str(Pubkey.from_string(mint))

                        buy_price = get_token_price(bonding_curve)
                        tp_price = buy_price * TAKE_PROFIT
                        sl_price = buy_price * STOP_LOSS
                        if balance >= BUY_AMOUNT:
                            # buy(mint, BUY_AMOUNT, 5)
                            update_balance(-BUY_AMOUNT)
                        else:
                            print("\033[91mNot enough balance to buy!\033[0m")
                            continue

                        

                        min_price, max_price = generate_price(buy_price)
                        start_price = buy_price


                        print(f"Bought at {buy_price}. Target TP: {tp_price}, SL: {sl_price}")
                        
                        start_time = time.time()  # Засекаем время входа в цикл
                        while True:
                            await asyncio.sleep(5)  # Запрашиваем цену раз в 5 секунд
                            current_price = get_token_price(bonding_curve)
                            print(f"Current price: {current_price}")

                            if current_price >= tp_price:
                                print(f"\033[92mTP reached! Selling at {current_price}\033[0m")
                                #sell(mint_pubkey, 100, 5)
                                update_balance(BUY_AMOUNT * TAKE_PROFIT)

                                price_diff = (current_price - start_price) / start_price
                                print(f"Price difference: {price_diff * 100:.2f}%")
                                record_trade(trade_history, min_price, max_price, delay1, delay2, price_diff)


                                break

                            if current_price <= sl_price:
                                print(f"\033[91mSL reached! Selling at {current_price}\033[0m")
                                #sell(mint_pubkey, 100, 5)
                                update_balance(BUY_AMOUNT * STOP_LOSS)

                                price_diff = (current_price - start_price) / start_price
                                print(f"Price difference: {price_diff * 100:.2f}%")
                                record_trade(trade_history, min_price, max_price, delay1, delay2, price_diff)

                                break

                            if time.time() - start_time >= delay2:
                                print(f"\033[93mTimeout reached! Selling at {current_price}\033[0m")
                                # sell(mint_pubkey, 100, 5)
                                update_balance(BUY_AMOUNT * current_price / buy_price)  # Продажа по текущей цене


                                price_diff = (current_price - start_price) / start_price
                                print(f"Price difference: {price_diff * 100:.2f}%")
                                record_trade(trade_history, min_price, max_price, delay1, delay2, price_diff)

                                break

                        print("Trade cycle completed. Restarting search for new token...")
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"WebSocket closed unexpectedly: {e}. Reconnecting in 5 seconds...")
                        await asyncio.sleep(5)
                        break

        except websockets.exceptions.InvalidStatusCode as e:
            print(f"WebSocket error: {e}. Server might be down. Retrying in 10 seconds...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Trade tokens on Solana.")
    parser.add_argument("--yolo", action="store_true", help="Run in YOLO mode (continuous trading)")
    args = parser.parse_args()

    asyncio.run(trade())

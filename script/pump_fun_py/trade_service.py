import asyncio
import json
import base64
import struct
import websockets
import os
import time
import requests
from datetime import datetime

from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from construct import Struct, Int64ul, Flag

from config import *
from coin_data import get_coin_data, sol_for_tokens, tokens_for_sol

EXPECTED_DISCRIMINATOR = struct.pack("<Q", 6966180631402821399)
TOKEN_DECIMALS = 6
WEBSOCKET_TIMEOUT = 30
RECONNECT_DELAY = 5

TAKE_PROFIT = 1.24  # +24%
STOP_LOSS = 0.92    # -8%

FILENAME = "trades_backup.json"

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

def round_float(value, decimals=10):
    return round(value, decimals)

def load_backup():
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            return json.load(f)
    return {}

def save_backup(data):
    with open(FILENAME, "w") as f:
        json.dump(data, f, indent=4)

def record_trade(data, min_price, max_price, buy_delay, sell_delay, result):
    key = (round_float(min_price), round_float(max_price), buy_delay, sell_delay)
    key_str = str(key)
    if key_str not in data:
        data[key_str] = []
    data[key_str].append(result)
    save_backup(data)

def update_balance(change):
    color = "\033[92m" if change > 0 else "\033[91m"
    print(f"{color}Balance change: {change:.6f} SOL\033[0m")

def generate_times():
    buy_delay = 5
    sell_delay = 20
    return buy_delay, sell_delay

def generate_price(price):
    step = 0.1e-08
    min_price = (price // step) * step
    max_price = min_price + 0.1e-08
    return min_price, max_price

def get_pump_curve_state(curve_address: str) -> BondingCurveState:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [str(curve_address), {"encoding": "base64"}]
    }

    for attempt in range(3):
        response = requests.post(RPC, json=payload).json()
        value = response.get("result", {}).get("value")

        if value and "data" in value and value["data"]:
            data_b64 = value["data"][0]
            data = base64.b64decode(data_b64)

            if data[:8] != EXPECTED_DISCRIMINATOR:
                raise ValueError("Invalid curve state discriminator")

            return BondingCurveState(data)

        print(f"Warning: No data for bonding curve {curve_address}, attempt {attempt + 1}/3")
        time.sleep(2)

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
            break
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed: {e}. Reconnecting...")
            break

async def trade(user_id, public_key, payer_keypair, position_size, slippage_tolerance, trade_history):
    print(f"Starting trade cycle for user {user_id}, wallet {public_key}")
    try:
        async with websockets.connect(WSS_ENDPOINT, ping_interval=20, ping_timeout=10) as websocket:
            args = await listen_for_create_transaction(websocket)
            if not args:
                return

            mint = args['mint']
            bonding_curve = args['bondingCurve']
            associated_bonding_curve = args['associatedBondingCurve']

            print(bonding_curve)

            delay1, delay2 = generate_times()
            await asyncio.sleep(delay1)

            mint_pubkey = str(Pubkey.from_string(mint))

            # Эмуляция покупки
            try:
                buy_price = get_token_price(bonding_curve)
            except ValueError as e:
                print(f"Skipping trade for {mint} due to {e}")
                return

            print(buy_price)

            print(f"Emulating buy for {mint} with {position_size:.6f} SOL")
            # Не вызываем update_balance здесь, только логируем покупку
            min_price, max_price = generate_price(buy_price)
            start_price = buy_price

            tp_price = buy_price * TAKE_PROFIT
            sl_price = buy_price * STOP_LOSS
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
                    print(f"Emulating sell for {mint}")
                    profit = position_size * (current_price / buy_price - 1)
                    # Вызываем только один раз с итоговым PNL
                    update_balance(profit)
                    price_diff = (current_price - start_price) / start_price
                    record_trade(trade_history, min_price, max_price, delay1, delay2, price_diff)
                    return

                if current_price <= sl_price:
                    print(f"\033[91mSL reached! Selling at {current_price}\033[0m")
                    print(f"Emulating sell for {mint}")
                    loss = position_size * (current_price / buy_price - 1)
                    # Вызываем только один раз с итоговым PNL
                    update_balance(loss)
                    price_diff = (current_price - start_price) / start_price
                    record_trade(trade_history, min_price, max_price, delay1, delay2, price_diff)
                    return

                if time.time() - start_time >= delay2:
                    print(f"\033[93mTimeout reached! Selling at {current_price}\033[0m")
                    print(f"Emulating sell for {mint}")
                    profit_loss = position_size * (current_price / buy_price - 1)
                    # Вызываем только один раз с итоговым PNL
                    update_balance(profit_loss)
                    price_diff = (current_price - start_price) / start_price
                    record_trade(trade_history, min_price, max_price, delay1, delay2, price_diff)
                    return

    except Exception as e:
        print(f"Error in trade for {public_key}: {e}")
        await asyncio.sleep(5)
        return
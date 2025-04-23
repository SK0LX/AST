import asyncio
import asyncpg
import websockets
import json
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from trade_service import trade, update_balance, record_trade, load_backup, save_backup
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
from solana.rpc.async_api import AsyncClient
from config import RPC

load_dotenv()

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432))
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

wallet_store = {}
trade_tasks = {}
trade_history = load_backup()

def format_wallet_info(public_key, wallet_data):
    pub_key_short = public_key[:8]
    priv_key_short = f"{wallet_data['private_key'][:4]}...{wallet_data['private_key'][-4:]}" if wallet_data['private_key'] else "N/A"
    position_size = wallet_data['position_size']
    trade_amount = wallet_data['balance'] * (position_size / 100)
    slippage_tolerance = wallet_data['slippage_tolerance']
    
    position_str = f"{position_size:.2f}% ({trade_amount:.6f} SOL)"
    slippage_str = f"{slippage_tolerance}%"
    
    return (
        f"Wallet: {pub_key_short}\n"
        f"  User ID: {wallet_data['user_id']}\n"
        f"  Private Key: {priv_key_short}\n"
        f"  Position Size: {position_str}\n"
        f"  Slippage: {slippage_str}\n"
        f"  Active: {wallet_data['is_trading_active']}\n"
        f"  Balance: {wallet_data['balance']:.6f} SOL\n"
        f"  Last Trade: {wallet_data['last_trade_time'] or 'Never'}\n"
        f"  Trade Count: {wallet_data['trade_count']}\n"
        f"  PnL: {wallet_data['pnl']:.6f} SOL"
    )

def format_wallet_store(wallet_store):
    if not wallet_store:
        return "No wallets in store"
    return "\n\n".join([format_wallet_info(pk, data) for pk, data in wallet_store.items()])

async def get_user_wallets(pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, public_key, position_size, slippage_tolerance, is_trading_active "
            "FROM wallets WHERE is_trading_active = true"
        )
        return [{
            "user_id": str(row["user_id"]),
            "public_key": row["public_key"],
            "private_key": wallet_store.get(row["public_key"], {}).get("private_key", ""),
            "position_size": row["position_size"],
            "slippage_tolerance": row["slippage_tolerance"],
            "is_trading_active": row["is_trading_active"]
        } for row in rows if row["public_key"] in wallet_store]

async def update_trade_stats(pool, public_key, pnl, is_success):
    logger.info(f"Updating trade stats for {public_key[:8]}: PNL={pnl:.6f}, Success={is_success}")
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO trades_stats (public_key, trade_date, date, pnl, is_success)
                VALUES ($1, NOW(), CURRENT_DATE, $2, $3)
                ON CONFLICT (public_key, trade_date) DO UPDATE
                SET pnl = trades_stats.pnl + $2,
                    is_success = $3
            """, public_key, pnl, is_success)
    except Exception as e:
        logger.error(f"Failed to update trade stats for {public_key[:8]}: {e}")

async def get_balance(public_key):
    client = AsyncClient(RPC)
    try:
        pubkey = Pubkey.from_string(public_key)
        balance_resp = await client.get_balance(pubkey)
        return balance_resp.value / 1e9
    finally:
        await client.close()

async def trade_wrapper(user_wallet, pool, trade_history):
    user_id = user_wallet["user_id"]
    public_key = user_wallet["public_key"]
    private_key = user_wallet["private_key"]
    position_size_percent = user_wallet["position_size"]
    slippage_tolerance = user_wallet["slippage_tolerance"]

    def patched_update_balance(change):
        update_balance(change)
        is_success = change > 0
        wallet_store[public_key]["balance"] += change
        wallet_store[public_key]["pnl"] += change
        wallet_store[public_key]["trade_count"] += 1
        wallet_store[public_key]["last_trade_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        asyncio.create_task(update_trade_stats(pool, public_key, change, is_success))
        logger.info(f"Balance updated for {public_key[:8]}:\n{format_wallet_info(public_key, wallet_store[public_key])}")

    def patched_record_trade(data, min_price, max_price, buy_delay, sell_delay, result):
        record_trade(data, min_price, max_price, buy_delay, sell_delay, result)
        logger.info(f"Trade recorded for {public_key[:8]}")

    import trade_service
    trade_service.update_balance = patched_update_balance
    trade_service.record_trade = patched_record_trade

    while wallet_store[public_key]["is_trading_active"]:
        try:
            payer_keypair = Keypair.from_base58_string(private_key)
            balance = wallet_store[public_key]["balance"]
            trade_amount = balance * (position_size_percent / 100)
            if trade_amount > balance:
                logger.error(f"Not enough balance ({balance:.6f} SOL) for {trade_amount:.6f} SOL trade!")
                await asyncio.sleep(5)
                continue
            logger.info(f"Starting trade for user {user_id}, wallet {public_key[:8]} with {trade_amount:.6f} SOL")
            await trade(user_id, public_key, payer_keypair, trade_amount, slippage_tolerance, trade_history)
        except Exception as e:
            logger.error(f"Trade failed for user {user_id}, wallet {public_key[:8]}: {e}")
            await asyncio.sleep(5)

async def update_balances(pool):
    while True:
        for public_key in wallet_store:
            try:
                balance = await get_balance(public_key)
                wallet_store[public_key]["balance"] = balance
                logger.info(f"Balance updated for {public_key[:8]}:\n{format_wallet_info(public_key, wallet_store[public_key])}")
            except Exception as e:
                logger.error(f"Failed to update balance for {public_key[:8]}: {e}")
        await asyncio.sleep(60)

async def sync_wallet_store(pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM wallets")
        for row in rows:
            pk = row["public_key"]
            if pk in wallet_store:
                wallet_store[pk]["user_id"] = str(row["user_id"])
                wallet_store[pk]["position_size"] = row["position_size"] if row["position_size"] is not None else wallet_store[pk]["position_size"]
                wallet_store[pk]["slippage_tolerance"] = row["slippage_tolerance"] if row["slippage_tolerance"] is not None else wallet_store[pk]["slippage_tolerance"]
                wallet_store[pk]["is_trading_active"] = row["is_trading_active"]

async def handle_websocket(websocket, pool):
    try:
        async for message in websocket:
            logger.info(f"Received WebSocket message: {message}")
            data = json.loads(message)
            action = data.get("action")
            public_key = data.get("publicKey")

            if action == "wallet:added":
                user_id = data["userId"]
                for existing_pk, wallet in list(wallet_store.items()):
                    if wallet["user_id"] == user_id and existing_pk != public_key:
                        logger.info(f"Removing old wallet {existing_pk[:8]} for user {user_id}")
                        del wallet_store[existing_pk]
                        if existing_pk in trade_tasks:
                            trade_tasks[existing_pk].cancel()
                            del trade_tasks[existing_pk]

                async with pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT * FROM wallets WHERE public_key = $1", public_key)
                    position_size = float(data.get("positionSize", 25))
                    slippage_tolerance = float(data.get("slippageTolerance", 2))
                    balance = await get_balance(public_key)
                    if row:
                        wallet_store[public_key] = {
                            "user_id": str(row["user_id"]),
                            "private_key": data["privateKey"],
                            "position_size": row["position_size"] if row["position_size"] is not None else position_size,
                            "slippage_tolerance": row["slippage_tolerance"] if row["slippage_tolerance"] is not None else slippage_tolerance,
                            "is_trading_active": row["is_trading_active"],
                            "balance": balance,
                            "last_trade_time": None,
                            "trade_count": 0,
                            "pnl": 0.0
                        }
                    else:
                        wallet_store[public_key] = {
                            "user_id": user_id,
                            "private_key": data["privateKey"],
                            "position_size": position_size,
                            "slippage_tolerance": slippage_tolerance,
                            "is_trading_active": False,
                            "balance": balance,
                            "last_trade_time": None,
                            "trade_count": 0,
                            "pnl": 0.0
                        }
                        private_key_preview = f"****{data['privateKey'][-4:]}"
                        await conn.execute("""
                            INSERT INTO wallets (user_id, public_key, private_key_preview, position_size, slippage_tolerance, is_trading_active)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (public_key) DO UPDATE
                            SET user_id = $1, private_key_preview = $3, position_size = $4, slippage_tolerance = $5, is_trading_active = $6
                        """, user_id, public_key, private_key_preview, position_size, slippage_tolerance, False)
                logger.info(f"Wallet added:\n{format_wallet_info(public_key, wallet_store[public_key])}")

            elif action == "bot:start":
                active_wallets = await get_user_wallets(pool)
                wallet = next((w for w in active_wallets if w["public_key"] == public_key), None)
                if wallet and public_key not in trade_tasks:
                    wallet_store[public_key]["is_trading_active"] = True
                    task = asyncio.create_task(trade_wrapper(wallet, pool, trade_history))
                    trade_tasks[public_key] = task
                    logger.info(f"Bot started for {public_key[:8]}:\n{format_wallet_info(public_key, wallet_store[public_key])}")

            elif action == "bot:stop" and public_key in trade_tasks:
                trade_tasks[public_key].cancel()
                trade_tasks.pop(public_key)
                wallet_store[public_key]["is_trading_active"] = False
                logger.info(f"Bot stopped for {public_key[:8]}:\n{format_wallet_info(public_key, wallet_store[public_key])}")

            elif action == "get_status":
                status = 'inactive'
                if public_key in wallet_store:
                    status = 'linking' if not wallet_store[public_key]["is_trading_active"] else 'active'
                await websocket.send(json.dumps({"action": "status", "publicKey": public_key, "status": status}))

            await sync_wallet_store(pool)
            logger.info(f"Current wallet store:\n{format_wallet_store(wallet_store)}")

    except websockets.ConnectionClosed:
        logger.info("WebSocket connection closed")

async def main():
    logger.info(f"Connecting to database with config: {DB_CONFIG}")
    pool = await asyncpg.create_pool(**DB_CONFIG)
    if not pool:
        logger.error("Failed to connect to database")
        return
    logger.info("Database pool created successfully")
    asyncio.create_task(update_balances(pool))
    async with websockets.serve(lambda ws: handle_websocket(ws, pool), "localhost", 8765):
        logger.info("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
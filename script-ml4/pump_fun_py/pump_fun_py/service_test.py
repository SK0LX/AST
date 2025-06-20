import asyncio
import struct
import json
from typing import *
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Processed
from solana.rpc.types import TokenAccountOpts, TxOpts
from solders.pubkey import Pubkey
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.instruction import Instruction, AccountMeta
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from spl.token.instructions import (
    CloseAccountParams,
    close_account,
    create_associated_token_account,
    get_associated_token_address,
)

# Constants from your first code
RPC_URL: Final[str] = "https://api.mainnet-beta.solana.com"
TOKEN_MINT: Final[str] = "2wCq7hyuFiidyd4GrFFBobKJuf1trzr3iZTppLmab6KT"
PUMP_PROGRAM_ID: Final[Pubkey] = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
LAMPORTS_PER_SOL: Final[int] = 1_000_000_000
TOKEN_DECIMALS: Final[int] = 6
EXPECTED_DISCRIMINATOR: Final[bytes] = struct.pack("<Q", 6966180631402821399)  # Pump.fun bonding curve discriminator
POLL_INTERVAL: Final[int] = 10  # Seconds between each status check

# Constants from your second code
GLOBAL: Pubkey = Pubkey.from_string("4wTV1YmiEkRvAtNtwAY6A1S1rb9hcsPMLY6am6JuiqYR")
FEE_RECIPIENT: Pubkey = Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEQ4nn3sgL69KH97KDUHbXVS")
SYSTEM_PROGRAM: Pubkey = Pubkey.from_string("11111111111111111111111111111111")
TOKEN_PROGRAM: Pubkey = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
RENT: Pubkey = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
EVENT_AUTHORITY: Pubkey = Pubkey.from_string("Ce6TQqeH7tBRXKyG5q6Htjtd4s65vCEudXXAt1X1AnkF")
PUMP_FUN_PROGRAM: Pubkey = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
ASSOC_TOKEN_ACC_PROG: Pubkey = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

# From first code: Bonding curve status functions
def get_associated_bonding_curve_address(mint: Pubkey, program_id: Pubkey) -> Pubkey:
    return Pubkey.find_program_address([b"bonding-curve", bytes(mint)], program_id)[0]

async def get_account_data(client: AsyncClient, pubkey: Pubkey) -> bytes:
    resp = await client.get_account_info(pubkey, encoding="base64")
    if not resp.value or not resp.value.data:
        raise ValueError(f"Account {pubkey} not found or has no data")
    return resp.value.data

def parse_curve_state(data: bytes) -> dict:
    if data[:8] != EXPECTED_DISCRIMINATOR:
        raise ValueError("Invalid discriminator for bonding curve")
    fields = struct.unpack_from("<QQQQQ?", data, 8)
    return {
        "virtual_token_reserves": fields[0] / 10**TOKEN_DECIMALS,
        "virtual_sol_reserves": fields[1] / LAMPORTS_PER_SOL,
        "real_token_reserves": fields[2] / 10**TOKEN_DECIMALS,
        "real_sol_reserves": fields[3] / LAMPORTS_PER_SOL,
        "token_total_supply": fields[4] / 10**TOKEN_DECIMALS,
        "complete": fields[5],
    }

async def check_bonding_curve_status(token_mint: str, rpc_url: str = RPC_URL) -> float:
    mint_pubkey = Pubkey.from_string(token_mint)
    curve_pubkey = get_associated_bonding_curve_address(mint_pubkey, PUMP_PROGRAM_ID)
    
    async with AsyncClient(rpc_url) as client:
        data = await get_account_data(client, curve_pubkey)
        state = parse_curve_state(data)
        
        if state["token_total_supply"] == 0:
            return 0.0
            
        return 100 - (100 * state["real_token_reserves"] / state["token_total_supply"])

# From second code: Buy/Sell functions (simplified, assuming dependencies exist)
async def get_token_price(mint_str: str, client: AsyncClient) -> float:
    """
    Get token price in SOL based on bonding curve data.
    """
    # Note: get_coin_data not provided; assuming it returns similar data to parse_curve_state
    async with AsyncClient(RPC_URL) as client:
        mint_pubkey = Pubkey.from_string(mint_str)
        curve_pubkey = get_associated_bonding_curve_address(mint_pubkey, PUMP_PROGRAM_ID)
        data = await get_account_data(client, curve_pubkey)
        state = parse_curve_state(data)
        
        virtual_sol_reserves = state["virtual_sol_reserves"]
        virtual_token_reserves = state["virtual_token_reserves"]
        
        if virtual_token_reserves == 0:
            return 0.0
        
        return virtual_sol_reserves / virtual_token_reserves

async def subscribe_to_new_tokens() -> None:
    """
    Subscribe to Pump.fun program logs to detect new token creation and monitor them.
    """
    client = AsyncClient(RPC_URL)
    websocket_url = RPC_URL.replace("https", "wss")
    active_tokens: list[str] = []  # Track active token mints
    token_data: Dict[str, dict] = {}  # Cache token info
    poll_interval = 10  # Seconds between checks
    progress_threshold = 80.0  # Sell at 80% progress
    price_threshold = 0.0001  # Sell at 0.0001 SOL price

    print("Subscribing to Pump.fun token creation logs...")

    async with connect(websocket_url) as ws:
        # Subscribe to logs for Pump.fun program, looking for 'initialize' instruction
        await ws.logs_subscribe(
            {"mentions": [str(PUMP_PROGRAM_ID)]},
            commitment="finalized"
        )
        first_resp = await ws.recv()  # Initial subscription response
        subscription_id = first_resp.result  # Get subscription ID

        while True:
            try:
                # Check for new logs
                resp = await asyncio.wait_for(ws.recv(), timeout=poll_interval)
                if hasattr(resp, "value"):
                    for log in resp.value.logs:
                        # Look for 'initialize' instruction (Pump.fun token creation)
                        if "initialize" in log.lower():
                            try:
                                # Extract mint from log (simplified; adjust based on actual log format)
                                log_parts = log.split()
                                for part in log_parts:
                                    try:
                                        mint = Pubkey.from_string(part)
                                        mint_str = str(mint)
                                        if mint_str not in active_tokens:
                                            active_tokens.append(mint_str)
                                            print(f"New token detected: {mint_str}")
                                            # Buy immediately (0.01 SOL)
                                            success = buy(mint_str, sol_in=0.01, slippage=5)
                                            if success:
                                                print(f"Bought tokens for {mint_str}")
                                            else:
                                                print(f"Failed to buy tokens for {mint_str}")
                                        break
                                    except Exception:
                                        continue
                            except Exception as e:
                                print(f"Error parsing log for mint: {e}")

                # Monitor active tokens
                for mint_str in active_tokens[:]:  # Copy to allow removal
                    try:
                        # Get progress and price
                        progress = await check_bonding_curve_status(mint_str, RPC_URL)
                        price = await get_token_price(mint_str, client)

                        # Store and display status
                        token_data[mint_str] = {"progress": progress, "price": price}
                        print(f"\nToken: {mint_str}")
                        print(f"Progress: {progress:.2f}%")
                        print(f"Price: {price:.8f} SOL")

                        # Check thresholds
                        if progress >= progress_threshold:
                            print(f"Progress threshold ({progress_threshold}%) reached!")
                            success = sell(mint_str, percentage=100, slippage=5)
                            if success:
                                print(f"Sold tokens for {mint_str}")
                                active_tokens.remove(mint_str)
                            else:
                                print(f"Failed to sell tokens for {mint_str}")

                        if price >= price_threshold:
                            print(f"Price threshold ({price_threshold} SOL) reached!")
                            success = sell(mint_str, percentage=50, slippage=5)
                            if success:
                                print(f"Sold 50% of tokens for {mint_str}")
                            else:
                                print(f"Failed to sell tokens for {mint_str}")

                    except Exception as e:
                        print(f"Error monitoring {mint_str}: {e}")

            except asyncio.TimeoutError:
                # No new logs, continue monitoring
                continue
            except Exception as e:
                print(f"Error in subscription loop: {e}")

    await client.close()
    print("Subscription closed.")

# Run the subscription
if __name__ == "__main__":
    try:
        asyncio.run(subscribe_to_new_tokens())
    except KeyboardInterrupt:
        print("Stopped by user.")
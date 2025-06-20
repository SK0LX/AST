from solana.rpc.async_api import AsyncClient
import websockets
import asyncpg

class AppContext:
    def __init__(self):
        self.solana: AsyncClient = None
        self.ws = None

    async def init(self):
        self.solana = AsyncClient("https://mainnet.helius-rpc.com/?api-key=0c503158-dced-43ab-9330-2d1a30098b95")
        self.ws = await websockets.connect("wss://pumpportal.fun/api/data")
        
    async def close(self):
        await self.solana.close()
        await self.ws.close()
       

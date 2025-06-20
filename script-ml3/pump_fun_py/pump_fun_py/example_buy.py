from pump_fun import buy
from config import *
# Buy Example
mint_str = "Gam7qWTQ32PcBYXQBiKfNArZgWLXubHjYGxLN7eLpump"
sol_in = 0.005
slippage = 5
buy(payer_keypair, mint_str, sol_in, slippage)
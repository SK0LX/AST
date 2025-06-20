from pump_fun import sell
from config import *


# Sell Example
mint_str = "GWHG2XwitknDNxCYyQQN2zEj59RHgxk3R7QuoFTuHVfH"
percentage = 100
slippage = 5
sell(payer_keypair, mint_str, percentage, slippage)
from pump_fun import sell
from config import *


# Sell Example
mint_str = "FyYMhjegSFBtbymZV7g6Wi4VqZhPhJ4picj8vHWypump"
percentage = 100
slippage = 5
sell(payer_keypair, mint_str, percentage, slippage)
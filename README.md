# AST: sniper bot 

## Idea  
AutoGraph is a tool for automatic token sniping with filtering before purchase.  

## Features  

- **Monitoring** — tracks new tokens in real time.  
- **Filtering** — blacklist, price limits, and transaction limits.  
- **Automation** — buy, hold, and sell based on strategy.  
- **Notifications** — Telegram, Android app.  
- **Logging** — analyzes trade efficiency.  

## Architecture  

### Core (JavaScript)  
- Processes incoming token streams.  
- Sends data for filtering.  
- Stores results in PostgreSQL.  

### Web Admin Panel (JavaScript)  
- Moderation interface: accept, reject, edit.  
- Settings: data sources, filtering.  

### Telegram Bot (Python)  
- Management via commands and buttons.  

### Mathematical Statistics (Python)  
- Trade analysis.  
- Strategy efficiency evaluation.  

### Android App (Kotlin)  
- Notifications.  
- Monitoring.  

### Database (PostgreSQL)  
- Stores token and transaction data.  
- Logs user actions.  
- Filtering metadata.  

## Roadmap  

- **MVP** — launch with basic filtering.  
- **Further development** — liquidity analysis, scam protection.

# pump_fun_py

Python library to trade on pump.fun. 

Updated: 1/24/2025

solana Version: 0.36.1

solders Version: 0.23.0

Clone the repo, and add your Private Key (Base58 string) and RPC to the config.py.


### Contact

-PF Token Launchers (Bundler or Self-Sniper)

-Bump Bot

-gRPC Detection (Mints, Buys, Migrations)

-Vanity Address Generator

-Rust implementations of PF code


### FAQS

**What format should my private key be in?** 

The private key should be in the base58 string format, not bytes. 

**Why are my transactions being dropped?** 

You get what you pay for. Don't use the main-net RPC, just spend the money for Helius or Quick Node.

**How do I change the fee?** 

Modify the UNIT_BUDGET and UNIT_PRICE in the config.py. 

**Does this code work on devnet?**

No. 


## Why It Works  

- Faster and more accurate than manual trading.  
- Filters reduce risks.  
- Statistics help adapt strategy.  

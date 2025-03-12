# AutoGraph: Automatic Token Sniping  

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

## Why It Works  

- Faster and more accurate than manual trading.  
- Filters reduce risks.  
- Statistics help adapt strategy.  

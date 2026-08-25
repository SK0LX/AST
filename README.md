# AST — Sniper Bot

Торговый бот для pump.fun в сети Solana: слушает появление новых токенов,
прогоняет их через фильтры и совершает сделку раньше, чем это успел бы сделать
человек. Управление — через веб-панель, Telegram или Android-приложение.

![Python](https://img.shields.io/badge/Python-asyncio-3776AB?style=flat-square&logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-Express-339933?style=flat-square&logo=nodedotjs&logoColor=white)
![Solana](https://img.shields.io/badge/Solana-web3-9945FF?style=flat-square&logo=solana&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-OTP-DC382D?style=flat-square&logo=redis&logoColor=white)
![Kotlin](https://img.shields.io/badge/Kotlin-Android-7F52FF?style=flat-square&logo=kotlin&logoColor=white)

> ⚠️ Проект исследовательский. Торговля на пампах — крайне рискованное занятие,
> потерять депозит здесь проще, чем заработать. Код опубликован как пример
> архитектуры, а не как инвестиционная рекомендация.

## Как работает

```
   pump.fun (WebSocket)
          │  новые минты, покупки, миграции
          ▼
   ┌─────────────┐    не прошёл     ┌──────────┐
   │   Фильтры   │─────────────────▶│  отбой   │
   │ blacklist,  │                  └──────────┘
   │ лимиты цены │
   └──────┬──────┘
          │ прошёл
          ▼
   ┌─────────────┐      сделка      ┌──────────────┐
   │   Trader    │─────────────────▶│    Solana    │
   │  asyncio    │◀─────────────────│              │
   └──────┬──────┘     результат    └──────────────┘
          │
          ▼
   PostgreSQL (PnL, история)  ──▶  Веб-панель · Telegram · Android
```

Бот держит постоянное WebSocket-соединение и реагирует на события в реальном
времени. Каждый пользователь торгует со своим кошельком и своими лимитами —
`trade_wrapper` изолирует сделку конкретного пользователя, а балансы и статистика
синхронизируются отдельными фоновыми задачами.

## Компоненты

| Каталог | Стек | Назначение |
|---|---|---|
| `script/` | Python, asyncio, asyncpg | Ядро: WebSocket, сделки, PnL, синхронизация кошельков |
| `script-stats/`, `script-stats-SE/` | Python | Сбор и разбор статистики сделок, оценка стратегий |
| `www/` | Node.js, Express, WebSocket | Веб-панель: авторизация, кошельки, дашборд, запуск бота |
| `AST/` | Kotlin, Retrofit | Android-приложение: уведомления и мониторинг |
| `db/` | Docker Compose | PostgreSQL, Redis, pgAdmin, Redis Commander |

### Ядро

```python
async def trade_wrapper(user_wallet, pool, trade_history): ...
async def update_balances(pool): ...
async def sync_wallet_store(pool): ...
async def handle_websocket(websocket, pool): ...
```

Всё асинхронно: пока одна сделка ждёт подтверждения в сети, обрабатываются
остальные события. Подпись транзакций — через `solders`, ключ пользователя
загружается в память только на время сделки.

### Веб-панель

Express + PostgreSQL + Redis. Вход по одноразовому коду (OTP хранится в Redis
с TTL), сессии, добавление кошелька, включение и выключение бота, дашборд с
текущими позициями. Реальное время — через WebSocket.

### Android

Retrofit-клиент к той же панели, фоновый сервис и push-уведомления о сделках.

## Безопасность ключей

Приватный ключ кошелька **не хранится в репозитории и не попадает в базу целиком**.
В PostgreSQL пишется только превью — последние 4 символа (`private_key_preview`),
чтобы пользователь мог отличить свои кошельки. Полный ключ живёт в рантайме
процесса-трейдера.

## Развёртывание

**1. Инфраструктура:**

```bash
cd db && docker compose up -d
```

Поднимутся PostgreSQL, Redis и веб-интерфейсы к ним. Схема базы — на
[ERD](db/ERD.jpg), описание — в [db/db.md](db/db.md).

**2. Веб-панель:**

```bash
cd www && npm install && npm start
```

**3. Ядро бота:**

```bash
cd script/pump_fun_py
pip install -r requirements.txt
python trade_manager.py
```

Понадобится собственный RPC-эндпоинт — публичная mainnet-нода не выдерживает
нагрузки и роняет транзакции.

## Структура

```
AST/
├── script/pump_fun_py/     # ядро: trade_manager, trade_service
├── script-stats/           # статистика сделок
├── script-stats-SE/        # вариант со стратегией SE
├── script-def/             # базовая конфигурация
├── www/                    # веб-панель
│   ├── src/                # index.js, auth.js, db.js
│   └── public/             # login.html, main.html, wallet.js
├── AST/                    # Android-приложение
└── db/                     # docker-compose, ERD, описание схемы
```

## Планы

- Анализ ликвидности перед входом
- Защита от скам-контрактов
- Разбор эффективности стратегий на исторических данных

## Зависимости

Взаимодействие с pump.fun построено на библиотеке
[`pump_fun_py`](https://github.com/1f1n/pump_fun_py) — она вендорится в каталогах
`script*` и адаптирована под многопользовательский сценарий.

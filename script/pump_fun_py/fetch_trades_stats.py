import asyncio
import asyncpg
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из .env
load_dotenv()

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432))
}

async def insert_test_data(pool):
    public_key = "6TBUoxmwNptbzTUx4xAfLFuL7yVmWNvAghdEHxtk1Jzz"
    trade_date = datetime.now()  # Текущая дата и время
    date = trade_date.date()     # Только дата
    pnl = -0.000187              # Пример PNL из твоих логов
    is_success = False           # Неудачная сделка

    async with pool.acquire() as conn:
        logger.info("Acquired DB connection for insert")
        try:
            await conn.execute("""
                INSERT INTO trades_stats (public_key, trade_date, date, pnl, is_success)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (public_key, trade_date) DO UPDATE
                SET pnl = $4, is_success = $5
            """, public_key, trade_date, date, pnl, is_success)
            logger.info(f"Inserted test data: public_key={public_key}, trade_date={trade_date}, pnl={pnl:.6f}, is_success={is_success}")
        except Exception as e:
            logger.error(f"Failed to insert test data: {e}")

async def fetch_trades_stats(pool):
    async with pool.acquire() as conn:
        logger.info("Acquired DB connection for fetch")
        rows = await conn.fetch("""
            SELECT * FROM trades_stats
            ORDER BY public_key ASC, trade_date ASC
        """)
        
        if not rows:
            logger.info("No records found in trades_stats")
        else:
            logger.info(f"Found {len(rows)} records in trades_stats")
            for row in rows:
                logger.info(
                    f"public_key: {row['public_key']}, "
                    f"trade_date: {row['trade_date']}, "
                    f"date: {row['date']}, "
                    f"pnl: {row['pnl']:.6f}, "
                    f"is_success: {row['is_success']}"
                )

async def main():
    logger.info(f"Connecting to database with config: {DB_CONFIG}")
    try:
        pool = await asyncpg.create_pool(**DB_CONFIG)
        if not pool:
            logger.error("Failed to create database pool")
            return

        logger.info("Database pool created successfully")
        
        # Вставляем тестовые данные
        await insert_test_data(pool)
        
        # Проверяем содержимое таблицы
        await fetch_trades_stats(pool)
        
        await pool.close()
        logger.info("Database pool closed")

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
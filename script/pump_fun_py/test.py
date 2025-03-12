import random
import json
import os

FILENAME = "trades_backup.json"

def round_float(value, decimals=10):
    """Округляет число с плавающей точкой до указанного количества знаков."""
    return round(value, decimals)

def load_backup():
    """Загружает историю сделок из файла, если он существует."""
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            return json.load(f)
    return {}

def save_backup(data):
    """Сохраняет историю сделок в файл."""
    with open(FILENAME, "w") as f:
        json.dump(data, f, indent=4)

def record_trade(data, min_price, max_price, buy_delay, sell_delay, result):
    """Записывает результат сделки в историю."""
    key = (
        round_float(min_price), 
        round_float(max_price), 
        buy_delay, 
        sell_delay
    )
    key_str = str(key)  # JSON не поддерживает кортежи как ключи
    
    if key_str not in data:
        data[key_str] = []

    data[key_str].append(result)
    save_backup(data)


def generate_values(price):
    step = 0.4e-08
    min_price = (price // step) * step
    max_price = min_price + 0.4e-08

    buy_delay_values = list(range(10, 61, 15))
    sell_delay_values = list(range(10, 61, 15))

    buy_delay = random.choice(buy_delay_values)
    sell_delay = random.choice(sell_delay_values)

    return min_price, max_price, buy_delay, sell_delay










# Загрузка истории сделок
trade_history = load_backup()

# Пример записи новой сделки
for i in range(1000):
    price = random.uniform(2.8e-08, 2.8e-07)
    min_price, max_price, buy_delay, sell_delay = generate_values(price)
    result = random.randint(-10,10)

    record_trade(trade_history, min_price, max_price, buy_delay, sell_delay, result)

# Проверка
print(trade_history)




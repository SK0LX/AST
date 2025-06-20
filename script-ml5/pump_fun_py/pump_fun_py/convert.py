import json

# Читаем исходный файл
with open('backup.json', 'r') as file:
    data = json.load(file)

# Обрабатываем данные
for item in data:
    # Преобразуем initial_buy
    if isinstance(item['initial_buy'], str):
        item['initial_buy'] = float(item['initial_buy'].replace(' SOL', ''))
    
    # Преобразуем market_cap
    if isinstance(item['market_cap'], str):
        item['market_cap'] = float(item['market_cap'].replace(' SOL', ''))

# Сохраняем в новый файл
with open('backup_cleared.json', 'w') as file:
    json.dump(data, file, indent=4)
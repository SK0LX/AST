#!/bin/bash

while true; do
    python3 trade_stats.py
    echo "Процесс завершился. Перезапуск через 5 секунд..."
    sleep 5
done

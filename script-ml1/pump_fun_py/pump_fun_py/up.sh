#!/bin/bash

while true; do
    python trade_service.py
    echo "Процесс завершился. Перезапуск через 50 секунд..."
    sleep 50
done

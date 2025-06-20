import pandas as pd
import json

# Чтение JSON
with open("backup_cleared.json", "r") as f:
    data = json.load(f)

# Преобразование в DataFrame
df = pd.DataFrame(data)
df["target"] = (df["result"] >= 0).astype(int)  # 1 если прибыль/безубыток

# Сохранение в CSV
df[["initial_buy", "market_cap", "price", "sol_amount", "target"]].to_csv("trades.csv", index=False)
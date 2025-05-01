"""
Стратегический оптимизатор для Pump-Fun бота.
--------------------------------------------
Использует trades_backup.json и выбирает buy_delay / sell_delay,
максимизируя ожидаемую прибыль с учётом риска.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List, Tuple, Any, Optional

JSON_PATH = Path(__file__).with_name("trades_backup.json")

StrategyKey = Tuple[float, float, int, int]   # min_price, max_price, buy_delay, sell_delay
Metrics     = Dict[str, float]

# ---------- util ----------------------------------------------------------- #

def _load_history(file: Path = JSON_PATH) -> Dict[str, List[float]]:
    if not file.exists():
        return {}
    with file.open() as f:
        return json.load(f)


def _parse_key(key_str: str) -> StrategyKey:
    return eval(key_str)  # ключи формировались как str(tuple)


# ---------- метрики -------------------------------------------------------- #

def _compute_metrics(pnls: List[float]) -> Metrics:
    n             = len(pnls)
    wins          = sum(1 for p in pnls if p > 0)
    losses        = sum(1 for p in pnls if p <= 0)
    pnl_pos_sum   = sum(p for p in pnls if p > 0) or 1e-9
    pnl_neg_sum   = abs(sum(p for p in pnls if p < 0)) or 1e-9
    mu            = mean(pnls)
    sigma         = stdev(pnls) if n > 1 else 1e-9
    profit_factor = pnl_pos_sum / pnl_neg_sum
    sharpe_like   = mu / sigma
    win_rate      = wins / n
    max_dd        = min(0, _max_drawdown(pnls))

    return {
        "n": n,
        "win_rate": win_rate,
        "avg_pnl": mu,
        "profit_factor": profit_factor,
        "sharpe_like": sharpe_like,
        "max_drawdown": max_dd,
    }


def _max_drawdown(pnls: List[float]) -> float:
    cum, peak, dd = 0.0, 0.0, 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        dd   = min(dd, cum - peak)
    return dd


# ---------- скоринг -------------------------------------------------------- #

def _score(m: Metrics) -> float:
    """Композитный рейтинг: ↑ Win-Rate, ↑ Avg PNL, ↑ Profit-Factor, ↓ Max DD."""
    sample_weight = 1.0 - math.exp(-m["n"] / 30)      # 0→1 при ~30+ сделках
    risk_penalty  = 1.0 + abs(m["max_drawdown"])      # чем глубже просадка, тем хуже
    return sample_weight * (
        0.5 * m["win_rate"] +
        0.3 * (m["avg_pnl"]  ) +
        0.2 * (m["profit_factor"] / risk_penalty)
    )


# ---------- публичный API -------------------------------------------------- #

class StrategyOptimizer:
    def __init__(self, path: Path = JSON_PATH) -> None:
        self.raw: Dict[str, List[float]] = _load_history(path)
        self.metrics: Dict[StrategyKey, Metrics] = {}
        self._calc()

    # ---- интерфейс ---- #
    def best(self, price: float) -> Optional[Tuple[StrategyKey, Metrics]]:
        """
        Вернуть лучшую стратегию для цены, попадающей в диапазон (min_price, max_price].
        """
        candidates = [(k, m) for k, m in self.metrics.items()
                      if k[0] <= price <= k[1]]
        if not candidates:
            return None
        return max(candidates, key=lambda kv: kv[1]["score"])

    def suggest(self, price: float) -> Optional[Dict[str, Any]]:
        """
        Удобная обёртка: {'buy_delay': 5, 'sell_delay': 20, 'info': metrics}
        """
        res = self.best(price)
        if res is None:
            return None
        key, metrics = res
        _, _, buy_d, sell_d = key
        return {"buy_delay": buy_d, "sell_delay": sell_d, "info": metrics}

    # ---- приватное ---- #
    def _calc(self) -> None:
        for key_str, pnls in self.raw.items():
            key = _parse_key(key_str)
            m   = _compute_metrics(pnls)
            m["score"] = _score(m)
            self.metrics[key] = m
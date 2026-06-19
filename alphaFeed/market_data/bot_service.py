import contextlib
import io
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

TRADER_DIR = Path(__file__).resolve().parents[2] / 'trader'
if str(TRADER_DIR) not in sys.path:
    sys.path.insert(0, str(TRADER_DIR))

from bot import GoldBot
from ml_model import MLModel, fetch_real_gold_data


@dataclass
class BacktestResult:
    total_pnl: Decimal
    win_rate: Decimal
    total_trades: int
    final_balance: Decimal
    events: list


def _money(value):
    return Decimal(str(round(float(value), 2)))


def run_gold_backtest(period='60d', interval='15m', initial_balance=10000):
    """Run the gold ML backtest and return structured metrics for Django."""
    # The trader module is print-heavy; keep worker logs readable and return structured data instead.
    with contextlib.redirect_stdout(io.StringIO()):
        data = fetch_real_gold_data(period=period, interval=interval)
        if data.empty or len(data) < 260:
            raise ValueError('Not enough market data returned for the configured backtest window.')

        split_idx = int(len(data) * 0.7)
        train_data = data.iloc[:split_idx]
        test_data = data.iloc[split_idx:]

        model = MLModel(horizon=16)
        model.train(train_data)

        bot = GoldBot(initial_balance=initial_balance, ml_model=model)
        window_size = 200
        for i in range(window_size, len(test_data)):
            window = test_data.iloc[i-window_size:i+1]
            bot.run_iteration(window)

    total_pnl = sum(bot.trades) if bot.trades else 0
    win_rate = (len([trade for trade in bot.trades if trade > 0]) / len(bot.trades) * 100) if bot.trades else 0

    return BacktestResult(
        total_pnl=_money(total_pnl),
        win_rate=Decimal(str(round(float(win_rate), 2))),
        total_trades=len(bot.trades),
        final_balance=_money(bot.risk_manager.balance),
        events=getattr(bot, 'trade_events', []),
    )

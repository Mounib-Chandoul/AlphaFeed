import logging
from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from .bot_service import run_gold_backtest
from .models import BotRun, Ticker, TradeHistory

logger = logging.getLogger(__name__)


def _get_ticker(symbol):
    defaults = {'name': 'Gold Spot / U.S. Dollar' if symbol == 'XAUUSD' else symbol}
    return Ticker.objects.get_or_create(symbol=symbol, defaults=defaults)[0]


@shared_task(bind=True, max_retries=1, default_retry_delay=120)
def execute_trading_bot_iteration(self, ticker_symbol='XAUUSD'):
    """Record one lightweight signal event. This does not place live broker orders."""
    logger.info('Starting trading bot signal scan for %s', ticker_symbol)
    ticker = _get_ticker(ticker_symbol)
    trade = TradeHistory.objects.create(
        ticker=ticker,
        side=TradeHistory.SIDE_LONG,
        price=Decimal('2350.50'),
        source='SIGNAL_SCAN',
    )
    return {'trade_id': trade.id, 'message': f'Signal scan recorded for {ticker_symbol}'}


@shared_task(bind=True, max_retries=0)
def run_backtest_job(self, bot_run_id):
    """Run the ML gold backtest and persist aggregate metrics plus trade events."""
    bot_run = BotRun.objects.get(id=bot_run_id)
    bot_run.status = BotRun.STATUS_RUNNING
    bot_run.started_at = timezone.now()
    bot_run.error_message = ''
    bot_run.save(update_fields=['status', 'started_at', 'error_message'])

    try:
        result = run_gold_backtest(
            period=bot_run.period,
            interval=bot_run.interval,
            initial_balance=float(bot_run.initial_balance),
        )

        ticker = _get_ticker(bot_run.ticker_symbol)
        trades = []
        for event in result.events:
            trades.append(TradeHistory(
                ticker=ticker,
                bot_run=bot_run,
                side=event.get('side', TradeHistory.SIDE_RESULT),
                price=Decimal(str(event.get('exit_price') or event.get('entry_price') or 0)),
                pnl=Decimal(str(event.get('pnl'))) if event.get('pnl') is not None else None,
                balance=Decimal(str(event.get('balance'))) if event.get('balance') is not None else None,
                source='BACKTEST',
            ))
        if trades:
            TradeHistory.objects.bulk_create(trades)

        bot_run.status = BotRun.STATUS_SUCCEEDED
        bot_run.finished_at = timezone.now()
        bot_run.total_pnl = result.total_pnl
        bot_run.win_rate = result.win_rate
        bot_run.total_trades = result.total_trades
        bot_run.final_balance = result.final_balance
        bot_run.save(update_fields=[
            'status', 'finished_at', 'total_pnl', 'win_rate', 'total_trades', 'final_balance'
        ])
        return {'status': bot_run.status, 'bot_run_id': bot_run.id}
    except Exception as exc:
        logger.exception('Backtest job failed for BotRun %s', bot_run_id)
        bot_run.status = BotRun.STATUS_FAILED
        bot_run.finished_at = timezone.now()
        bot_run.error_message = str(exc)
        bot_run.save(update_fields=['status', 'finished_at', 'error_message'])
        raise

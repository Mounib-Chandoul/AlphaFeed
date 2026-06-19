from django.db import models


class Ticker(models.Model):
    symbol = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ['symbol']

    def __str__(self):
        return self.symbol


class PriceHistory(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'price history'

    def __str__(self):
        return f"{self.ticker.symbol} @ {self.price}"


class BotRun(models.Model):
    STATUS_QUEUED = 'QUEUED'
    STATUS_RUNNING = 'RUNNING'
    STATUS_SUCCEEDED = 'SUCCEEDED'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
    ]

    RUN_BACKTEST = 'BACKTEST'
    RUN_SIGNAL = 'SIGNAL'
    RUN_TYPE_CHOICES = [
        (RUN_BACKTEST, 'Backtest'),
        (RUN_SIGNAL, 'Signal scan'),
    ]

    run_type = models.CharField(max_length=16, choices=RUN_TYPE_CHOICES, default=RUN_BACKTEST)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    ticker_symbol = models.CharField(max_length=16, default='XAUUSD')
    task_id = models.CharField(max_length=255, blank=True)
    period = models.CharField(max_length=16, default='60d')
    interval = models.CharField(max_length=16, default='15m')
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000)
    final_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_pnl = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_trades = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_run_type_display()} {self.ticker_symbol} {self.status}"


class TradeHistory(models.Model):
    SIDE_LONG = 'LONG'
    SIDE_SHORT = 'SHORT'
    SIDE_RESULT = 'RESULT'
    SIDE_CHOICES = [
        (SIDE_LONG, 'Long'),
        (SIDE_SHORT, 'Short'),
        (SIDE_RESULT, 'Result'),
    ]

    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    bot_run = models.ForeignKey(BotRun, on_delete=models.SET_NULL, null=True, blank=True, related_name='trades')
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    pnl = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    source = models.CharField(max_length=24, default='BOT')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'trade history'

    def __str__(self):
        return f"{self.ticker.symbol} {self.side} @ {self.price}"

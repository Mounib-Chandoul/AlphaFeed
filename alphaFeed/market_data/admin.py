from django.contrib import admin

from .models import BotRun, Ticker, PriceHistory, TradeHistory


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name')
    search_fields = ('symbol', 'name')


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'price', 'timestamp')
    list_filter = ('ticker', 'timestamp')
    search_fields = ('ticker__symbol',)
    readonly_fields = ('timestamp',)


@admin.register(BotRun)
class BotRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'run_type', 'ticker_symbol', 'status', 'total_trades', 'total_pnl', 'win_rate', 'created_at')
    list_filter = ('run_type', 'status', 'created_at')
    search_fields = ('ticker_symbol', 'task_id')
    readonly_fields = ('created_at', 'started_at', 'finished_at')


@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'side', 'price', 'pnl', 'balance', 'source', 'timestamp')
    list_filter = ('ticker', 'side', 'source', 'timestamp')
    search_fields = ('ticker__symbol',)
    readonly_fields = ('timestamp',)

from django.db import DatabaseError
from django.db.models import Count
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from .models import BotRun, Ticker, TradeHistory
from .tasks import execute_trading_bot_iteration, run_backtest_job
from django.views.generic import ListView
from django.views import View


def trigger_bot(request):
    """Queue a trading bot signal scan via HTTP."""
    ticker = request.GET.get('ticker', 'XAUUSD')

    try:
        task = execute_trading_bot_iteration.delay(ticker)
        return JsonResponse({
            'status': 'queued',
            'message': f'Trading bot signal scan queued for {ticker}',
            'task_id': task.id
        })
    except Exception as exc:
        return JsonResponse({
            'status': 'error',
            'message': 'The worker queue is unavailable. Start Redis and a Celery worker, then try again.',
            'detail': str(exc),
        }, status=503)


def LandingPageView(request):
    return render(request, 'landing.html')


class TickerListView(ListView):
    model = Ticker
    template_name = 'market_data/ticker_list.html'
    context_object_name = 'tickers'

    def get_queryset(self):
        self.database_unavailable = False
        try:
            return list(Ticker.objects.order_by('symbol'))
        except DatabaseError:
            self.database_unavailable = True
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['database_unavailable'] = getattr(self, 'database_unavailable', False)
        return context


class RunAnalysisView(View):
    def get(self, request):
        try:
            bot_run = BotRun.objects.create(run_type=BotRun.RUN_BACKTEST, ticker_symbol='XAUUSD')
            task = run_backtest_job.delay(bot_run.id)
            bot_run.task_id = getattr(task, 'id', '') or ''
            bot_run.save(update_fields=['task_id'])
            return redirect(f"{reverse('dashboard')}?run={bot_run.id}")
        except Exception as exc:
            return HttpResponse(
                f"Unable to queue backtest. Start Redis and a Celery worker, then try again. Detail: {exc}",
                status=503,
            )


def dashboard_view(request):
    database_unavailable = False

    try:
        trades = list(TradeHistory.objects.select_related('ticker', 'bot_run').order_by('-timestamp')[:12])
        runs = list(BotRun.objects.order_by('-created_at')[:6])
        latest_run = runs[0] if runs else None
        total_trades = TradeHistory.objects.count()
        tracked_assets = Ticker.objects.count()
        long_count = TradeHistory.objects.filter(side=TradeHistory.SIDE_LONG).count()
        short_count = TradeHistory.objects.filter(side=TradeHistory.SIDE_SHORT).count()
        latest_trade = TradeHistory.objects.select_related('ticker').order_by('-timestamp').first()
        side_mix = list(TradeHistory.objects.values('side').annotate(total=Count('id')).order_by('side'))
    except DatabaseError:
        database_unavailable = True
        trades = []
        runs = []
        latest_run = None
        total_trades = 0
        tracked_assets = 0
        long_count = 0
        short_count = 0
        latest_trade = None
        side_mix = []

    return render(request, 'dashboard.html', {
        'trades': trades,
        'runs': runs,
        'latest_run': latest_run,
        'total_trades': total_trades,
        'tracked_assets': tracked_assets,
        'long_count': long_count,
        'short_count': short_count,
        'latest_trade': latest_trade,
        'side_mix': side_mix,
        'database_unavailable': database_unavailable,
    })

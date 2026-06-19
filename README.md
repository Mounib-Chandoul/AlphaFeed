# AlphaFeed

AlphaFeed is a Django SaaS dashboard for running and monitoring a gold trading research bot. The production path is Django + Celery + Redis + PostgreSQL. The bot integration currently runs signal scans and ML backtests; it does not place live broker orders.

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp alphaFeed/.env.example alphaFeed/.env
# For local sqlite, remove DB_ENGINE and the DB_* variables from alphaFeed/.env.
python alphaFeed/manage.py migrate
python alphaFeed/manage.py createsuperuser
```

Run the web app:

```bash
python alphaFeed/manage.py runserver 127.0.0.1:8000
```

Run Redis and Celery in separate shells:

```bash
redis-server
celery -A alphaFeed worker -l info --workdir alphaFeed
celery -A alphaFeed beat -l info --workdir alphaFeed
```

Open `http://127.0.0.1:8000/`, then use **Run backtest** on the dashboard.

## Production checklist

- Set `DJANGO_DEBUG=False`.
- Set a unique `DJANGO_SECRET_KEY`.
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for the deployed domain.
- Use PostgreSQL and Redis managed services or locked-down private containers.
- Run `python alphaFeed/manage.py migrate` during release.
- Run `python alphaFeed/manage.py collectstatic --noinput` during release.
- Serve Django with Gunicorn/Uvicorn behind an HTTPS reverse proxy.
- Run at least one Celery worker and one Celery beat process.
- Keep `alphaFeed/.env` out of git. Use `alphaFeed/.env.example` as the template.
- Add a real broker adapter before enabling live order placement. The current task records research signals and backtest events only.

## Process commands

Web:

```bash
gunicorn alphaFeed.wsgi:application --chdir alphaFeed --bind 0.0.0.0:8000
```

Worker:

```bash
celery -A alphaFeed worker -l info --workdir alphaFeed
```

Scheduler:

```bash
celery -A alphaFeed beat -l info --workdir alphaFeed
```

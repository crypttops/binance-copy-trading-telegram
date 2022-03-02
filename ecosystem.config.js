module.exports = {
  "apps": [
  {
    "name": "Binance-copy-trading-celery",
    "cwd": ".",
    "script": ".venv/bin/python",
    "args": "-m celery -A tasks.celery worker -l INFO -B",
    "instances": "1",
    "wait_ready": true,
    "autorestart": true,
    "max_restarts": 5
  },
  {
    "name": "binance-copy-trading-sub",
    "cwd": ".",
    "script": "copytradesubscribe.py",
    "instances": "1",
    "wait_ready": true,
    "autorestart": true,
    "max_restarts": 5,
    "interpreter" : ".venv/bin/python",
  },
  {
    "name": "binane-copy-trading-telegram-bot",
    "script": "trade_telegram_bot.py",
    "args": [],
    "instances": "1",
    "wait_ready": true,
    "autorestart": true,
    "max_restarts": 5,
    "interpreter" : ".venv/bin/python",
  }
]
};
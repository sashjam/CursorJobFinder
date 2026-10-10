"""Запуск десктоп-приложения JobDesk."""

from jobdesk.config import ensure_env_loaded
from jobdesk.gui.app import run_app

if __name__ == "__main__":
    ensure_env_loaded()
    run_app()

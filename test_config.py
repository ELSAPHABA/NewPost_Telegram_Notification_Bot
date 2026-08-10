import os
from contextlib import contextmanager

from config import get_proxy_manager, get_settings


ENV_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "USER_AGENTS_FILE",
    "USER_AGENT_ROTATE_INTERVAL",
    "WATCHER_WORKER_COUNT",
    "PROXY_ENABLED",
    "PROXY_USER",
    "PROXY_PASS",
    "PROXY_PORT",
    "PROXY_ROTATE_SECONDS",
] + [f"PROXY_HOST_{index}" for index in range(1, 13)]


@contextmanager
def env(values):
    old = {key: os.environ.get(key) for key in ENV_KEYS}
    try:
        for key in ENV_KEYS:
            os.environ.pop(key, None)
        os.environ.update(values)
        get_settings.cache_clear()
        get_proxy_manager.cache_clear()
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()
        get_proxy_manager.cache_clear()


def main():
    with env({"TELEGRAM_BOT_TOKEN": "token"}):
        assert get_proxy_manager().requests_proxies() is None

    with env(
        {
            "TELEGRAM_BOT_TOKEN": "token",
            "PROXY_ENABLED": "true",
            "PROXY_USER": "user@example.com",
            "PROXY_PASS": "p/a:ss",
            "PROXY_HOST_1": "http://proxy1.example.com:1234/path",
            "PROXY_HOST_2": "proxy2.example.com",
            "PROXY_PORT": "8080",
        }
    ):
        proxy_manager = get_proxy_manager()
        proxies = proxy_manager.requests_proxies()
        assert proxies["http"] == proxies["https"]
        assert proxies["http"].startswith("http://user%40example.com:p%2Fa%3Ass@")
        assert proxies["http"].endswith(":8080")
        before = proxies["http"]
        proxy_manager.rotate_now()
        assert proxy_manager.requests_proxies()["http"] != before


if __name__ == "__main__":
    main()

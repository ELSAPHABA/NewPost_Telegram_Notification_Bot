import os
import time
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None or value == "":
        return default

    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise RuntimeError(f"{name} must be one of: {', '.join(sorted(TRUE_VALUES | FALSE_VALUES))}")


def _env_int(name, default, minimum=1):
    value = os.getenv(name)
    if value is None or value == "":
        return default

    try:
        number = int(value)
    except ValueError as e:
        raise RuntimeError(f"{name} must be an integer.") from e

    if number < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}.")
    return number


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    chat_ids_file: str
    user_agents_file: str
    user_agent_rotate_interval: int
    watcher_worker_count: int
    proxy_enabled: bool
    proxy_user: str
    proxy_pass: str
    proxy_hosts: tuple[str, ...]
    proxy_port: str
    proxy_rotate_seconds: int

    def validate(self):
        if not self.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")

        if not self.proxy_enabled:
            return self

        missing = []
        if not self.proxy_user:
            missing.append("PROXY_USER")
        if not self.proxy_pass:
            missing.append("PROXY_PASS")
        if not self.proxy_hosts:
            missing.append("PROXY_HOST_1..PROXY_HOST_12")
        if not self.proxy_port:
            missing.append("PROXY_PORT")
        elif not self.proxy_port.isdigit():
            missing.append("PROXY_PORT(integer)")

        if missing:
            raise RuntimeError(f"Proxy is enabled but missing: {', '.join(missing)}")

        return self


class ProxyManager:
    def __init__(self, settings):
        self.settings = settings

    def requests_proxies(self):
        if not self.settings.proxy_enabled:
            return None

        host = self.settings.proxy_hosts[self._host_index()]
        user = quote(self.settings.proxy_user, safe="")
        password = quote(self.settings.proxy_pass, safe="")
        proxy_url = f"{self._proxy_scheme()}://{user}:{password}@{host}:{self.settings.proxy_port}"
        return {"http": proxy_url, "https": proxy_url}

    def _host_index(self):
        return int(time.monotonic() // self.settings.proxy_rotate_seconds) % len(self.settings.proxy_hosts)

    def _proxy_scheme(self):
        if self.settings.proxy_port == "1080" or any(".socks." in host for host in self.settings.proxy_hosts):
            return "socks5h"
        return "http"


def _proxy_hosts():
    hosts = []
    for index in range(1, 13):
        host = os.getenv(f"PROXY_HOST_{index}", "").strip()
        if host:
            hosts.append(_clean_host(host))
    return tuple(hosts)


def _clean_host(host):
    if "://" in host:
        host = host.split("://", 1)[1]
    return host.split("/", 1)[0]


@lru_cache
def get_settings():
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        chat_ids_file=os.getenv("CHAT_IDS_FILE", "chat_ids.json"),
        user_agents_file=os.getenv("USER_AGENTS_FILE", "user-agents.txt"),
        user_agent_rotate_interval=_env_int("USER_AGENT_ROTATE_INTERVAL", 20),
        watcher_worker_count=_env_int("WATCHER_WORKER_COUNT", 3),
        proxy_enabled=_env_bool("PROXY_ENABLED", False),
        proxy_user=os.getenv("PROXY_USER", ""),
        proxy_pass=os.getenv("PROXY_PASS", ""),
        proxy_hosts=_proxy_hosts(),
        proxy_port=os.getenv("PROXY_PORT", "").strip(),
        proxy_rotate_seconds=_env_int("PROXY_ROTATE_SECONDS", 1800),
    ).validate()


@lru_cache
def get_proxy_manager():
    return ProxyManager(get_settings())

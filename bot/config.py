import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    steam_api_key: str
    poll_interval: int
    bf6_appid: str


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    steam_api_key = os.getenv("STEAM_API_KEY", "").strip()
    # Steam key для шага 1 не обязателен, но пусть будет в конфиге:
    if not steam_api_key:
        steam_api_key = ""

    poll_interval = int(os.getenv("POLL_INTERVAL", "45"))
    bf6_appid = os.getenv("BF6_APPID", "2807960").strip()

    return Config(
        bot_token=bot_token,
        steam_api_key=steam_api_key,
        poll_interval=poll_interval,
        bf6_appid=bf6_appid,
    )

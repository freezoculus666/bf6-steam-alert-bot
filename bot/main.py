import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.config import load_config


async def on_start(message: Message) -> None:
    await message.answer(
        "👋 Я бот алертов Battlefield 6 (Steam).\n"
        "Пока я в режиме MVP.\n\n"
        "Дальше добавим команды /addsteam, /panel и мониторинг."
    )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config()
    bot = Bot(token=cfg.bot_token)
    dp = Dispatcher()

    dp.message.register(on_start, CommandStart())

    logging.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

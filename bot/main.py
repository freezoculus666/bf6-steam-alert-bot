import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.config import load_config
from bot.handlers import router
from bot.migrate import init_models
from bot.poller import poll_loop



async def on_start(message: Message) -> None:
    await message.answer(
        "👋 Я бот алертов Battlefield 6 (Steam).\n\n"
        "Команды:\n"
        "• /addsteam <steam_id> [имя]\n"
        "• /liststeam\n"
        "• /panel\n"
    )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config()
    await init_models()

    bot = Bot(token=cfg.bot_token)
    dp = Dispatcher()

    dp.message.register(on_start, CommandStart())
    dp.include_router(router)

    logging.info("Bot starting...")
    asyncio.create_task(poll_loop(bot, cfg))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

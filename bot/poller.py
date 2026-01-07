import asyncio
import logging

from sqlalchemy import select

from bot.config import Config
from bot.db import session_scope
from bot.models import Chat
from bot.panel import render_panel
from bot.repo import (
    get_panel_message_id,
    get_states_map,
    list_players,
    upsert_chat,
    upsert_player_state,
)
from bot.steam import get_player_summaries

logger = logging.getLogger(__name__)


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


async def poll_loop(bot, cfg: Config) -> None:
    # дать боту стартовать
    await asyncio.sleep(5)

    if not cfg.steam_api_key:
        logger.warning("STEAM_API_KEY is empty - polling will not work!")
        return

    while True:
        try:
            # 1) достаём все чаты
            async with session_scope() as session:
                rows = (await session.execute(select(Chat.chat_id))).all()
                chat_ids = [r[0] for r in rows]
                await session.commit()

            # 2) обходим чаты
            for chat_id in chat_ids:
                # список игроков
                async with session_scope() as session:
                    await upsert_chat(session, chat_id)
                    players = await list_players(session, chat_id)
                    panel_id = await get_panel_message_id(session, chat_id)
                    states = await get_states_map(session, chat_id)
                    await session.commit()

                steam_ids = [sid for sid, _ in players]
                if not steam_ids:
                    # нечего мониторить, но панель можно обновить
                    if panel_id:
                        try:
                            await bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=panel_id,
                                text=render_panel(players, states),
                                parse_mode="Markdown",
                            )
                        except Exception:
                            pass
                    continue

                # Steam API: батчим по 100
                summaries_all: dict[str, dict] = {}
                for batch in _chunks(steam_ids, 100):
                    summaries_all.update(await get_player_summaries(cfg.steam_api_key, batch))

                # 3) обновляем состояния + шлём алерты
                async with session_scope() as session:
                    for steam_id, name in players:
                        pdata = summaries_all.get(steam_id)
                        gameid = pdata.get("gameid") if pdata else None
                        is_playing_bf6 = str(gameid) == str(cfg.bf6_appid)

                        should_alert = await upsert_player_state(
                            session=session,
                            chat_id=chat_id,
                            steam_id=steam_id,
                            is_playing_bf6=is_playing_bf6,
                        )

                        if should_alert:
                            display = (name or (pdata.get("personaname") if pdata else None) or steam_id)
                            await bot.send_message(
                                chat_id,
                                f"🎮 **{display}** запустил **Battlefield 6**!",
                                parse_mode="Markdown",
                            )

                    await session.commit()

                # 4) обновляем панель (берём актуальные states после commit)
                if panel_id:
                    async with session_scope() as session:
                        players_now = await list_players(session, chat_id)
                        states_now = await get_states_map(session, chat_id)
                        await session.commit()

                    try:
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=panel_id,
                            text=render_panel(players_now, states_now),
                            parse_mode="Markdown",
                        )
                    except Exception:
                        pass

        except Exception:
            logger.exception("Polling error")

        await asyncio.sleep(cfg.poll_interval)

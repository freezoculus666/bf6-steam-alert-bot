import time
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Chat, Player, PlayerState


# -------------------------
# Chats
# -------------------------
async def upsert_chat(session: AsyncSession, chat_id: int) -> None:
    stmt = sqlite_insert(Chat).values(chat_id=chat_id).on_conflict_do_nothing(
        index_elements=[Chat.chat_id]
    )
    await session.execute(stmt)


async def set_panel_message_id(session: AsyncSession, chat_id: int, message_id: int) -> None:
    stmt = update(Chat).where(Chat.chat_id == chat_id).values(panel_message_id=message_id)
    await session.execute(stmt)


async def get_panel_message_id(session: AsyncSession, chat_id: int) -> Optional[int]:
    stmt = select(Chat.panel_message_id).where(Chat.chat_id == chat_id)
    row = (await session.execute(stmt)).first()
    return row[0] if row else None


async def clear_panel_message_id(session: AsyncSession, chat_id: int) -> None:
    stmt = update(Chat).where(Chat.chat_id == chat_id).values(panel_message_id=None)
    await session.execute(stmt)


# -------------------------
# Players
# -------------------------
async def add_player(
    session: AsyncSession,
    chat_id: int,
    steam_id: str,
    display_name: Optional[str],
) -> None:
    stmt = sqlite_insert(Player).values(
        chat_id=chat_id,
        steam_id=steam_id,
        display_name=display_name,
    ).on_conflict_do_update(
        index_elements=[Player.chat_id, Player.steam_id],
        set_={"display_name": display_name},
    )
    await session.execute(stmt)


async def list_players(session: AsyncSession, chat_id: int) -> list[tuple[str, Optional[str]]]:
    stmt = (
        select(Player.steam_id, Player.display_name)
        .where(Player.chat_id == chat_id)
        .order_by(Player.steam_id)
    )
    rows = (await session.execute(stmt)).all()
    return [(r[0], r[1]) for r in rows]


# -------------------------
# States
# -------------------------
async def get_states_map(session: AsyncSession, chat_id: int) -> dict[str, PlayerState]:
    """
    Возвращает словарь steam_id -> PlayerState для данного чата.
    """
    stmt = select(PlayerState).where(PlayerState.chat_id == chat_id)
    rows = (await session.execute(stmt)).scalars().all()
    return {r.steam_id: r for r in rows}


async def upsert_player_state(
    session: AsyncSession,
    chat_id: int,
    steam_id: str,
    is_playing_bf6: bool,
    alert_cooldown_sec: int = 300,
) -> bool:
    """
    Обновляет состояние игрока.
    Возвращает True, если нужно отправить алерт (первый вход в BF6 или после cooldown).

    alert_cooldown_sec: защита от "дребезга" статуса (по умолчанию 5 минут).
    """
    now = int(time.time())

    stmt = select(PlayerState).where(
        PlayerState.chat_id == chat_id,
        PlayerState.steam_id == steam_id,
    )
    state = (await session.execute(stmt)).scalar_one_or_none()

    # Если состояния нет — создаём
    if not state:
        state = PlayerState(
            chat_id=chat_id,
            steam_id=steam_id,
            was_playing_bf6=int(is_playing_bf6),
            since_ts=now if is_playing_bf6 else None,
            last_alert_ts=now if is_playing_bf6 else None,
        )
        session.add(state)
        return bool(is_playing_bf6)

    # Переход: не играл -> играет
    if is_playing_bf6 and not state.was_playing_bf6:
        state.was_playing_bf6 = 1
        state.since_ts = now

        # антифлуд: если уже алертили недавно, то не алертим снова
        last_alert = int(state.last_alert_ts) if state.last_alert_ts else 0
        if now - last_alert >= alert_cooldown_sec:
            state.last_alert_ts = now
            return True

        # даже если не алертим — обновим last_alert_ts не нужно
        return False

    # Всё ещё играет — ничего не меняем
    if is_playing_bf6 and state.was_playing_bf6:
        return False

    # Переход: играл -> не играет
    if (not is_playing_bf6) and state.was_playing_bf6:
        state.was_playing_bf6 = 0
        state.since_ts = None
        return False

    return False

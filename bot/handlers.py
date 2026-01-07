import re
from typing import Optional

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message

from bot.db import session_scope
from bot.panel import render_panel
from bot.repo import (
    add_player,
    get_panel_message_id,
    get_states_map,
    list_players,
    set_panel_message_id,
    upsert_chat,
)

router = Router()
STEAM_ID_RE = re.compile(r"^\d{17}$")


# -------------------------------------------------
# Helpers
# -------------------------------------------------
async def _is_admin(message: Message) -> bool:
    """
    Возвращает True, если пользователь админ/создатель чата.
    В private-чате всегда True.
    """
    if not message.chat or not message.from_user:
        return False

    if message.chat.type == "private":
        return True

    try:
        member = await message.bot.get_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
        )
        return member.status in ("administrator", "creator")
    except TelegramBadRequest:
        return False


async def _deny(message: Message) -> None:
    await message.answer("⛔ Эта команда доступна только администраторам группы.")


def _parse_addsteam_args(text: str) -> tuple[Optional[str], Optional[str]]:
    parts = text.split(maxsplit=2)
    if len(parts) < 2:
        return None, None
    steam_id = parts[1].strip()
    name = parts[2].strip() if len(parts) >= 3 else None
    return steam_id, name


# -------------------------------------------------
# Commands
# -------------------------------------------------
@router.message(Command("addsteam"))
async def cmd_addsteam(message: Message) -> None:
    if not await _is_admin(message):
        await _deny(message)
        return

    steam_id, name = _parse_addsteam_args(message.text or "")
    if not steam_id:
        await message.answer("Использование:\n`/addsteam <steam_id> [имя]`", parse_mode="Markdown")
        return

    if not STEAM_ID_RE.match(steam_id):
        await message.answer("SteamID должен состоять из **17 цифр**.", parse_mode="Markdown")
        return

    async with session_scope() as session:
        await upsert_chat(session, message.chat.id)
        await add_player(session, message.chat.id, steam_id, name)
        await session.commit()

    await message.answer("✅ Игрок добавлен / обновлён.")


@router.message(Command("liststeam"))
async def cmd_liststeam(message: Message) -> None:
    async with session_scope() as session:
        await upsert_chat(session, message.chat.id)
        players = await list_players(session, message.chat.id)
        await session.commit()

    if not players:
        await message.answer("Список пуст. Админ может добавить игроков через `/addsteam`.")
        return

    lines = ["📋 **Игроки:**"]
    for steam_id, name in players:
        label = name if name else steam_id
        lines.append(f"• {label} — `{steam_id}`")

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("panel"))
async def cmd_panel(message: Message) -> None:
    if not await _is_admin(message):
        await _deny(message)
        return

    async with session_scope() as session:
        await upsert_chat(session, message.chat.id)
        players = await list_players(session, message.chat.id)
        states = await get_states_map(session, message.chat.id)
        panel_id = await get_panel_message_id(session, message.chat.id)
        await session.commit()

    text = render_panel(players, states)

    # Если панель существует — редактируем
    if panel_id:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=panel_id,
                text=text,
            )
            await message.answer("✅ Панель обновлена.")
            return
        except TelegramBadRequest:
            panel_id = None

    # Иначе создаём новую
    msg = await message.answer(text, disable_notification=True)

    # Пытаемся закрепить
    try:
        await message.bot.pin_chat_message(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            disable_notification=True,
        )
    except TelegramBadRequest:
        pass

    async with session_scope() as session:
        await upsert_chat(session, message.chat.id)
        await set_panel_message_id(session, message.chat.id, msg.message_id)
        await session.commit()

    await message.answer("📌 Панель создана (и закреплена, если у бота есть права).")

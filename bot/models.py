from typing import Optional

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Chat(Base):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    panel_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    silent_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("chat_id", "steam_id", name="uq_chat_player"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    steam_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

from sqlalchemy import BigInteger

class PlayerState(Base):
    __tablename__ = "player_states"
    __table_args__ = (UniqueConstraint("chat_id", "steam_id", name="uq_chat_state"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    steam_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    was_playing_bf6: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    since_ts: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)       # unix ts
    last_alert_ts: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True) # unix ts

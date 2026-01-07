from typing import Iterable

import aiohttp

STEAM_SUMMARIES_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"


async def get_player_summaries(
    api_key: str,
    steam_ids: Iterable[str],
) -> dict[str, dict]:
    """
    Возвращает dict: steam_id -> player_data
    """
    if not steam_ids:
        return {}

    params = {
        "key": api_key,
        "steamids": ",".join(steam_ids),
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(STEAM_SUMMARIES_URL, params=params, timeout=10) as resp:
            resp.raise_for_status()
            data = await resp.json()

    players = data.get("response", {}).get("players", [])
    return {p["steamid"]: p for p in players}

"""
This module handles the processing and management of TagPro game replays.
It provides functionality to:
- Process unprocessed replays from a queue
- Retrieve replay data from the TagPro API
- Extract and analyze replay details including player stats, map info, and cap times
"""

from typing import Any, List, Optional

import httpx
import json
import time

import jsonutil


async def process_unprocessed_replays(stats_path, unproc_path, replays_dir, maps):
    """
    Process replays that are in the unprocessed queue.
    
    This function:
    1. Checks for replays that need processing & verifies they are not already downloaded
    2. Attempts to retrieve and validate replay data
    3. Extracts replay details and updates stats
    4. Saves successful replays to disk
    
    Args:
        stats_path: Path to the stats JSON file
        unproc_path: Path to the unprocessed replays JSON file
        replays_dir: Directory where replay files are stored
        maps: List of map configurations from the spreadsheet
    """
    stats = await jsonutil.read_json(stats_path)
    unproc = await jsonutil.read_json(unproc_path)
    # Get set of already downloaded replay UUIDs
    downloaded = {p.stem for p in replays_dir.iterdir() if p.is_file()}
    now = time.time()

    for uuid, info in list(unproc.items()):
        first, last = info["first"], info["last"]

        # Skip if already processed or downloaded
        if uuid in stats or uuid in downloaded:
            unproc.pop(uuid)
            continue

        # Only process if:
        # 1. Less than 24 hours since first attempt
        # 2. Enough time has passed since last attempt (1/4 of time since first attempt)
        if not (last - first <= 86_400 and now - last > (last - first) / 4):
            continue

        unproc[uuid]["last"] = now

        try:
            replay = await retrieve_replay_data(uuid)
        except RuntimeError:
            continue
        if not replay:
            continue

        details = get_replay_details(replay, maps)
        if not details:
            unproc.pop(uuid)
            continue

        # Save replay data and update stats
        (replays_dir / f"{uuid}.json").write_text(json.dumps(replay))
        stats[uuid] = details
        unproc.pop(uuid)

    await jsonutil.write_json(stats_path, stats)
    await jsonutil.write_json(unproc_path, unproc)


async def retrieve_replay_data(uuid: str) -> Optional[List[Any]]:
    """
    Retrieve replay data from the TagPro API.
    
    Makes two API calls:
    1. Get replay metadata and game ID
    2. Get the actual replay data using the game ID
    
    Args:
        uuid: The unique identifier for the replay
        
    Returns:
        List of replay events if successful, None otherwise
        
    Raises:
        RuntimeError: If rate limited or invalid JSON response
    """
    async with httpx.AsyncClient() as client:
        # First API call to get replay metadata
        r = await client.get(
            "https://tagpro.koalabeast.com/replays/data", params={"uuid": uuid}
        )
        if r.status_code == 429:
            raise RuntimeError("Rate limited")
        try:
            info = r.json()
        except ValueError:
            raise RuntimeError("Invalid JSON")
        games = info.get("games", [])
        if len(games) != 1:
            return None
            
        # Second API call to get actual replay data
        r2 = await client.get(
            "https://tagpro.koalabeast.com/replays/gameFile",
            params={"gameId": games[0]["id"]},
        )
    # Parse replay data into list of events
    replay = [json.loads(line) for line in r2.text.splitlines()]
    # Verify replay contains game start event
    if not any(e for e in replay if e[1] == "time" and e[2].get("state") == 1):
        return None
    return replay


def get_replay_details(replay: List[Any], maps: List[Any]) -> Optional[dict]:
    """
    Extract and analyze details from a replay.
    
    Processes replay data to extract:
    - Map information
    - Player details
    - Cap times and winning conditions
    - Chat messages and quotes
    
    Args:
        replay: List of replay events
        maps: List of map configurations from spreadsheet
        
    Returns:
        Dictionary containing replay details or None if invalid
    """
    # Verify replay structure
    assert replay[0][1] == "recorder-metadata"
    assert replay[2][1] == "map"
    assert replay[3][1] == "clientInfo"
    meta, map_d = replay[0][2], replay[2][2]
    
    # Extract map ID
    try:
        mid = replay[3][2]["mapfile"].split("/")[1]
    except Exception:
        mid = None

    # Find matching map configuration
    sm = [m for m in maps if m["map_id"] == mid]
    if not sm:
        sm = [m for m in maps if str(mid) in m.get("equivalent_map_ids", [])]
    if sm:
        m0 = sm[0]
        # Determine caps needed to win (infinity for pup maps)
        caps = float("inf") if m0.get("caps_to_win") == "pups" else int(m0.get("caps_to_win") or 1)
        allow_blue = bool(m0.get("allow_blue_caps"))
        eff = m0["map_id"]
    else:
        caps, eff, allow_blue = 1, mid, False

    # Find game start time
    try:
        t0 = next(t for t, e, d in replay if e == "time" and d.get("state") == 1)
    except StopIteration:
        return None

    # Extract player information
    players = {
        p["id"]: {
            "name": p["displayName"],
            "user_id": p["userId"],
            "is_red": p["team"] == 1,
        }
        for p in meta["players"]
    }

    def run_details():
        """Extract details about the winning cap and player."""
        for t, ev, caps_list in (x for x in replay if x[1] == "p"):
            for cd in caps_list:
                if cd.get("s-captures") != caps:
                    continue
                pl = players[cd["id"]]
                if not (pl["is_red"] or allow_blue):
                    continue
                rt = t - t0
                # Get last chat message from capping player
                chats = [m for m in replay if m[1] == "chat" and m[2].get("from") == cd["id"]]
                quote = chats[-1][2]["message"] if chats else None
                return rt, pl["name"], pl["user_id"], quote
        return None, None, None, None

    rt, uname, uid, quote = run_details()
    
    # Compile all replay details
    return {
        "map_id": eff,
        "actual_map_id": mid,
        "preset": None,
        "map_name": map_d["info"]["name"],
        "map_author": map_d["info"]["author"],
        "players": list(players.values()),
        "capping_player": uname,
        "capping_player_user_id": uid,
        "record_time": rt,
        "is_solo": len(players) == 1,
        "timestamp": meta["started"],
        "uuid": meta["uuid"],
        "caps_to_win": caps,
        "capping_player_quote": quote,
    }

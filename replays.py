from typing import Any, List, Optional

import httpx
import json
import time

import jsonutil


async def process_unprocessed_replays(stats_path, unproc_path, replays_dir, maps):
    stats = await jsonutil.read_json(stats_path)
    unproc = await jsonutil.read_json(unproc_path)
    downloaded = {p.stem for p in replays_dir.iterdir() if p.is_file()}
    now = time.time()

    for uuid, info in list(unproc.items()):
        first, last = info["first"], info["last"]

        if uuid in stats or uuid in downloaded:
            unproc.pop(uuid)
            continue

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

        (replays_dir / f"{uuid}.json").write_text(json.dumps(replay))
        stats[uuid] = details
        unproc.pop(uuid)

    await jsonutil.write_json(stats_path, stats)
    await jsonutil.write_json(unproc_path, unproc)


async def retrieve_replay_data(uuid: str) -> Optional[List[Any]]:
    async with httpx.AsyncClient() as client:
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
        r2 = await client.get(
            "https://tagpro.koalabeast.com/replays/gameFile",
            params={"gameId": games[0]["id"]},
        )
    replay = [json.loads(line) for line in r2.text.splitlines()]
    if not any(e for e in replay if e[1] == "time" and e[2].get("state") == 1):
        return None
    return replay


def get_replay_details(replay: List[Any], maps: List[Any]) -> Optional[dict]:
    assert replay[0][1] == "recorder-metadata"
    assert replay[2][1] == "map"
    assert replay[3][1] == "clientInfo"
    meta, map_d = replay[0][2], replay[2][2]
    try:
        mid = replay[3][2]["mapfile"].split("/")[1]
    except Exception:
        mid = None

    sm = [m for m in maps if m["map_id"] == mid]
    if not sm:
        sm = [m for m in maps if str(mid) in m.get("equivalent_map_ids", [])]
    if sm:
        m0 = sm[0]
        caps = float("inf") if m0.get("caps_to_win") == "pups" else int(m0.get("caps_to_win") or 1)
        allow_blue = bool(m0.get("allow_blue_caps"))
        eff = m0["map_id"]
    else:
        caps, eff, allow_blue = 1, mid, False

    try:
        t0 = next(t for t, e, d in replay if e == "time" and d.get("state") == 1)
    except StopIteration:
        return None

    players = {
        p["id"]: {
            "name": p["displayName"],
            "user_id": p["userId"],
            "is_red": p["team"] == 1,
        }
        for p in meta["players"]
    }

    def run_details():
        for t, ev, caps_list in (x for x in replay if x[1] == "p"):
            for cd in caps_list:
                if cd.get("s-captures") != caps:
                    continue
                pl = players[cd["id"]]
                if not (pl["is_red"] or allow_blue):
                    continue
                rt = t - t0
                chats = [m for m in replay if m[1] == "chat" and m[2].get("from") == cd["id"]]
                quote = chats[-1][2]["message"] if chats else None
                return rt, pl["name"], pl["user_id"], quote
        return None, None, None, None

    rt, uname, uid, quote = run_details()
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

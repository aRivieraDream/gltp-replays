import io, csv, requests, json, sys
from collections import defaultdict

def get_replay_data(uuid):
    response = requests.get(
        "https://tagpro.koalabeast.com/replays/data",
        params={"uuid": uuid}
    )
    if response.status_code == 429:
        raise RuntimeError
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError
    if len(data["games"]) != 1:
        return None
    response = requests.get(
        "https://tagpro.koalabeast.com/replays/gameFile",
        params={"gameId": data["games"][0]["id"]}
    )
    return [json.loads(line) for line in response.text.splitlines()]

def format_ms(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) / 1000
    return f"{minutes}:{seconds:06.3f}"

def get_hold_details(replay):
    metadata = next(r for r in replay if r[1] == "recorder-metadata")[2]
    players_info = {
        p["id"]: {
            "name": p["displayName"],
            "user_id": p["userId"],
            "is_red": p["team"] == 1
        }
        for p in metadata["players"]
    }

    holding_flags = {}
    player_hold_times = defaultdict(int)
    team_hold_times = defaultdict(int)

    stop_events = ("kill", "drop", "p")

    for tick in replay:
        time, event_type, data = tick

        if event_type == "tagproGrab":
            player_id = data["id"]
            if player_id not in holding_flags:
                holding_flags[player_id] = time

        elif event_type in stop_events:
            entries = data if isinstance(data, list) else [data]
            for d in entries:
                player_id = d.get("id")
                if player_id in holding_flags:
                    start = holding_flags.pop(player_id)
                    duration = time - start
                    player_hold_times[player_id] += duration
                    team_id = players_info[player_id]["team"]
                    team_hold_times[team_id] += duration

    red_team = {}
    blue_team = {}
    for pid, info in players_info.items():
        ms = player_hold_times.get(pid, 0)
        formatted = format_ms(ms)
        if info["team"] == 1:
            red_team[info["name"]] = formatted
        else:
            blue_team[info["name"]] = formatted

    return {
        "Red Total Hold Time": format_ms(team_hold_times[1]),
        "Blue Total Hold Time": format_ms(team_hold_times[2]),
        "Red Players": red_team,
        "Blue Players": blue_team
    }

if __name__ == "__main__":
    replay_data = get_replay_data(sys.argv[1])
    hold_details = get_hold_details(replay_data)
    print(json.dumps(hold_details, indent=4))

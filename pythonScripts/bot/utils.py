import datetime as dt
import logging
import json
import os
from rapidfuzz import fuzz
from maps import get_maps
from replay_manager import get_wr_entry


def setup_logger(name, filename):
    """Set up a logger with file handler and formatter."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def time_since(timestamp):
    """Convert timestamp to human-readable time ago string."""
    diff = dt.datetime.now() - dt.datetime.fromtimestamp(timestamp/1000)
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds // 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} hours ago"
    else:
        return f"{int(seconds // 86400)} days ago"


def timedelta_str(td):
    """Convert timedelta to formatted string."""
    return f"{td.seconds//3600:02d}:" * (td.total_seconds() >= 3600) + f"{(td.seconds%3600)//60:02d}:{td.seconds%60:02d}.{td.microseconds//1000:03d}"


def default_float(s, default=None):
    """Safely convert string to float with default fallback."""
    try:
        return float(s)
    except ValueError:
        return default


def get_game_info(preset):
    """Get formatted game information string for a given preset."""
    if preset is None:
        return "No current game preset set."
    
    curr_maps = [m for m in get_maps() if m["preset"] == preset]
    if not curr_maps:
        return f"Sorry, I don't know the MAP details for {preset}"
    
    details = curr_maps[0]
    msgs = [
        f"Playing '{details['name']}', Difficulty: {details['difficulty']},",
        f"Map ID: {details['map_id']}, Preset: {details['preset']}"
    ]
    
    if default_float(details['balls_req'], 100) > 1.0:
        msgs.append(f"YOU NEED {details['balls_req']} BALLS TO COMPLETE THIS MAP!")

    wr = get_wr_entry(details['map_id'])
    if wr:
        msgs.append(
            "WR: " + timedelta_str(dt.timedelta(seconds=wr['record_time'] / 1000)) +
            f" (Cap by {wr['capping_player']}) " +
            ("(Solo)" if wr['players'] == 1 else f"+{len(wr['players'])} others") +
            " | " + time_since(wr['timestamp']) +
            " | " + f"({details['caps_to_win'] or 1} cap(s) to finish)"
        )
        if wr['capping_player_quote']:
            msgs.append(f"WR Quote: '{wr['capping_player_quote']}'")
    else:
        msgs.append("(No world record less than 60 minutes recorded for this map)")
    
    return "\n".join(msgs)


def get_legal_maps(maps, settings, num_ready_balls):
    """Filter maps based on settings and number of ready players."""
    if settings["category"]:
        maps = [m for m in maps if settings["category"].lower() in m["category"].lower()]
    
    if settings["difficulty"]:
        low, high = float(settings["difficulty"][0] or 0.0), float(settings["difficulty"][1] or 100.0)
        maps = [m for m in maps if low <= default_float(m["difficulty"], 10) <= high]
    
    minfun = default_float(settings["minfun"], 0.0)
    maps = [m for m in maps if default_float(m["fun"], 100) >= minfun]
    
    maps = [m for m in maps if any(str(br) in m["balls_req"] for br in range((num_ready_balls or 1) + 1))]
    
    return maps


def find_best_info_message(query, periodic_messages):
    """Find the best matching info message for a given query."""
    return max(periodic_messages, key=lambda s: fuzz.partial_ratio(query.lower(), s.lower()))


def save_settings(settings, filename='bot_settings.json'):
    """Save settings to JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to save settings: {e}")
        return False


def load_settings(filename='bot_settings.json', default_settings=None):
    """Load settings from JSON file with fallback to defaults."""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                saved_settings = json.load(f)
            return saved_settings
    except Exception as e:
        print(f"Failed to load saved settings: {e}")
    
    return default_settings or {}

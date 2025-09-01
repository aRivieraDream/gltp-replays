# Constants and configuration for the TagPro bot

# Base URLs
BASE_URL = "https://tagpro.koalabeast.com"
GROUPS_URL = f"{BASE_URL}/groups/"
GAME_URL = f"{BASE_URL}/game"

# Room configuration
ROOM_NAME = "Val's buggy af lobby - kill me"
DISCORD_LINK = "discord.gg/Y3MZYdxV"

# Group settings
GROUP_SETTINGS = {
    "groupName": ROOM_NAME,
    "serverSelect": "false",
    "regions": "US Central",
    "discoverable": "true",
    "redTeamName": "Good",
    "blueTeamName": "Bad",
    "ghostMode": "noPlayerOrMarsCollisions"
}

# Default settings
DEFAULT_MAP_SETTINGS = {
    "category": None,
    "difficulty": (1.0, 3.5),
    "minfun": 3.0
}

DEFAULT_LOBBY_SETTINGS = {
    "region": "US Central",
    "discoverable": "true"
}

# User management
MODERATOR_NAMES = [
    "FWO", "DAD.", "TeaForYou&Me", "Some Ball 64", 
    "MRCOW", "Billy", "hmmmm", "Valerian", "3"
]

RESTRICTED_NAMES = ["Fap", "Ptuh", "marvin"]

# Region mapping
REGION_MAP = {
    "east": "US East",
    "central": "US Central", 
    "west": "US West",
    "eu": "Europe",
    "oce": "Oceanic",
    "oceanic": "Oceanic"
}

# Periodic messages for bot communication
PERIODIC_MESSAGES = [
    # Promotion
    f"Dont forget to join the GLTP Discord server! {DISCORD_LINK}",
    "Psssst... Hey you... yeah you.\nThink about this: Out of everyone you know, whos most likely to enjoy trying out gravity maps?\nPlease message them a link to this group.",
    "TP pubs dead? This lobby is open 24/7, and often active late at night!",
    "Gravity League TagPro has flexible timing, your team can run the maps when it works best for you!",

    # docs
    "If you want a new map go back to group and Ill load a fresh one!",
    "This lobby is open 24/7, but the best time to join is 10PM Eastern.",
    "The bot cycles through maps from this spreadsheet:\ndocs.google.com/spreadsheets/d/1OnuTCekHKCD91W39jXBG4uveTCCyMxf9Ofead43MMCU\nThere are currently {map_count} maps in rotation!",
    "Map too hard? \"SETTINGS difficulty 1 3\"  Too easy? \"SETTINGS difficulty 4 7\"",
    "Use \"SETTINGS category yourcategory\" to play specific map types!\nCategories include buddy, mars, non-grav, race, unlimited, tower, and more!",
    f"Please file bug reports and feature requests in the #bug-reports-and-suggestions room in {DISCORD_LINK}",
    f"Made or found a new map you'd like to see in rotation? Share it with us in {DISCORD_LINK}",
    f"World records are automatically updated for games which take place in this group.\nIf your record was in a different group, you can submit a link to #wr-submissions in {DISCORD_LINK}\nor simply say \"MEMO <replay uuid here>\"",
    "You can see all the bots commands by saying \"HELP\"",
    "Hey guys, you should check out the world records webpage: bambitp.github.io/GLTP/",

    # tip
    "Tip: **Hold up** for higher / floating jump, **Hold down** to short jump",
    "Tip: You can use the space bar to avoid AFK disconnecting",
    "Tip: Falling through a one-tile passage between a wall and a green gate?\n**Hold** up, slowly approach, and hug the wall while falling off.",
    "Tip: Need to jump fewer than 5 tiles? hold down before you **tap** jump",
    "Tip: You can get MAXIMUM jumping height by with a quick double tap, holding up on the 2nd jump.",
    "Tip: Gravity is quite hard at first, but after a few dozen games you'll be able to move like the pros.",

    # joke
    "Why is it dangerous to play tagpro while pooping?\nBecause tp runs out after 20 seconds.",
    "Why are honest Zoomers so bad at tagpro?\nBecause they aint even cappin.",
    "Why did the tagpro player go to jail?\nBecause he was an offender who wouldn't stop grabbing",
    "Fun fact: When you play on the Atlanta server you don't get \"popped\", you get \"coked\"",

    # lore
    "Lore: Grav once asked BartimaeusJr in a pub if he made BartJrs Gravity Challenge. BartimaeusJr denied it",
    "Lore: GLTPs roots lie with Dad and Madoka, the architects of its destiny, whose whispered ambitions shaped its foundation",
    "Lore: On March 3rd 2025, SB Army SB **destroyed** the TP refresh record,\naccumulating over 6,000 refreshes in a game",
    "Lore: FWO and Unity hold the current duo WR for most pops in one game with 20,000 pops",
    "Lore: FWO holds the current solo WR for most pops in one game with 12,000 pops",
    "Lore: There is a **rumor** that TeaForYou&Me used to be CoffeeForYou&Me",
    "Lore: The grav bot was originally created to manage an OFM lobby for 8v8 brownian-motion bots.",
    "Lore: Billy is the blue power ranger of tagpro",
    "Lore: Gravity, once was dead, with few active players, until TeaForYou&Me revived it as a game mode.",

    # troll
    "Please send TagproDad a Discord PM wishing them a good day!",
    "Unity, could you please stop doing that.",
    "MOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
    "I have a question guys, how many sides does a ball have?",
    "Some people mistakenly think I'm a bot, but in reality I'm just a dedicated group manager",
    "Current Gravity Map ELOs (based on previous 180 days)\n- Goated Muted SB: 1463\n- Dad: 1389\n- Unity: 1240\n- Madoka: 1235",
    "Quota for INFO command exceeded, ignoring INFO requests for next 48 hours",
]

# Browser configuration
CHROME_OPTIONS = [
    "--headless",
    "--disable-gpu", 
    "--no-sandbox",
    "--disable-notifications",
    "--disable-popup-blocking",
    "--disable-dev-shm-usage",
    "--remote-debugging-port=9222"
]

# Login mode configuration
LOGIN_MODE = True  # Set to True for manual login, False for normal operation
CHROME_PROFILE_DIR = "/app/chrome-profile/login"  # Persistent profile directory

# Platform-specific browser paths
CHROME_PATHS = {
    "Darwin": [  # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium"
    ],
    "Linux": [  # Linux
        "/usr/bin/google-chrome",           # System Chrome (preferred)
        "/usr/bin/chromium-browser",        # System Chromium
        "/snap/bin/chromium"               # Snap Chromium (fallback)
    ]
}

# Game timing constants
FINDING_GAME_TIMEOUT = 300  
GAME_END_TIMEOUT = 2  
PERIODIC_MESSAGE_INTERVAL = 1800  
PRESET_LOAD_INTERVAL = 5  #
LAUNCH_DELAY = 5  
GAME_STR_DELAY = 5  

# File paths
REPLAY_STATS_PATH = "data/replay_stats.json"

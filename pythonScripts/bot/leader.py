import datetime as dt
import time
import logging
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException

from rapidfuzz import fuzz

from replay_manager import write_replay_uuid, get_wr_entry
from maps import inject_map_id_into_preset, get_maps


def setup_logger(name, filename):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


# Create two loggers
event_logger = setup_logger("events_logger", "events.txt")
ws_logger = setup_logger("ws_logger", "ws.txt")


discord_link = "discord.gg/Y3MZYdxV"


def time_since(timestamp):
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
    return f"{td.seconds//3600:02d}:" * (td.total_seconds() >= 3600) + f"{(td.seconds%3600)//60:02d}:{td.seconds%60:02d}.{td.microseconds//1000:03d}"


def default_float(s, default=None):
    try:
        return float(s)
    except ValueError:
        return default


PERIODIC_MESSAGES = [
    # Promotion
    f"Dont forget to join the GLTP Discord server! {discord_link}",
    "Psssst... Hey you... yeah you.\nThink about this: Out of everyone you know, whos most likely to enjoy trying out gravity maps?\nPlease message them a link to this group.",
    "TP pubs dead? This lobby is open 24/7, and often active late at night!",
    "Gravity League TagPro has flexible timing, your team can run the maps when it works best for you!",


    # docs
    "If you want a new map go back to group and Ill load a fresh one!",
    "This lobby is open 24/7, but the best time to join is 10PM Eastern.",
    f"The bot cycles through maps from this spreadsheet:\ndocs.google.com/spreadsheets/d/1OnuTCekHKCD91W39jXBG4uveTCCyMxf9Ofead43MMCU\nThere are currently {len(get_maps())} maps in rotation!",
    "Map too hard? \"SETTINGS difficulty 1 3\"  Too easy? \"SETTINGS difficulty 4 7\"",
    "Use \"SETTINGS category yourcategory\" to play specific map types!\nCategories include buddy, mars, non-grav, race, unlimited, tower, and more!",
    f"Please file bug reports and feature requests in the #bug-reports-and-suggestions room in {discord_link}",
    f"Made or found a new map you'd like to see in rotation? Share it with us in {discord_link}",
    f"World records are automatically updated for games which take place in this group.\nIf your record was in a different group, you can submit a link to #wr-submissions in {discord_link}\nor simply say \"MEMO <replay uuid here>\"",
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


class DriverAdapter:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # Disable alerts and popups
        options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.set_capability("goog:chromeOptions", {"prefs": {"profile.default_content_setting_values.popups": 0}})
        options.set_capability("unhandledPromptBehavior", "dismiss")
        # Configure webdriver for cross-platform compatibility
        from selenium.webdriver.chrome.service import Service
        import platform
        import os
        
        # Add container-specific options
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        
        # Platform-specific browser paths
        if platform.system() == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium"
            ]
        else:  # Linux
            chrome_paths = [
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome"
            ]
        
        # Try each path until one works
        for path in chrome_paths:
            if os.path.exists(path):
                try:
                    print(f"Trying browser at: {path}")
                    service = Service(executable_path=path)
                    self.driver = webdriver.Chrome(options=options, service=service)
                    print(f"Successfully started browser from: {path}")
                    break
                except Exception as e:
                    print(f"Failed to start browser from {path}: {e}")
                    continue
        else:
            # If no path worked, try letting Selenium find it automatically
            try:
                print("Trying automatic browser detection...")
                self.driver = webdriver.Chrome(options=options)
                print("Successfully started browser with automatic detection")
            except Exception as e:
                print(f"Automatic detection failed: {e}")
                raise Exception("Could not start any webdriver")
        self.inject_ws_intercept()
        self.inject_auto_close_alerts()

        self.my_id = None
        self.event_handlers = {}

    def inject_ws_intercept(self):
        ws_injection_script = """
        if (!window.myWebSockets) {
            window.myWebSockets = {};
            window.myWsMessages = {};
            window.myWsCounter = 0;
            const OriginalWebSocket = window.WebSocket;
            window.WebSocket = function(url, protocols) {
                const ws = protocols ? new OriginalWebSocket(url, protocols) : new OriginalWebSocket(url);
                ws._id = window.myWsCounter++;
                window.myWebSockets[ws._id] = ws;
                window.myWsMessages[ws._id] = [];
                ws.addEventListener('message', function(event) {
                    let message = event.data;
                    let parsed = null;
                    try {
                        let commaIndex = message.indexOf(',');
                        if (commaIndex > -1) {
                            let payload = message.substring(commaIndex + 1);
                            parsed = JSON.parse(payload);
                        } else {
                            parsed = JSON.parse(message);
                        }
                    } catch(e) {
                        parsed = message;
                    }
                    window.myWsMessages[ws._id].push(parsed);
                });
                return ws;
            };
            window.WebSocket.prototype = OriginalWebSocket.prototype;
            window.WebSocket.CONNECTING = OriginalWebSocket.CONNECTING;
            window.WebSocket.OPEN = OriginalWebSocket.OPEN;
            window.WebSocket.CLOSING = OriginalWebSocket.CLOSING;
            window.WebSocket.CLOSED = OriginalWebSocket.CLOSED;
        }
        """
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": ws_injection_script})

    def inject_auto_close_alerts(self):
        alert_injection_script = """
        // Override native alert functions to auto-close any dialogs.
        window.alert = function(message) {
            console.log("Alert auto-closed: " + message);
        };
        window.confirm = function(message) {
            console.log("Confirm auto-closed: " + message);
            return true;
        };
        window.prompt = function(message, defaultValue) {
            console.log("Prompt auto-closed: " + message);
            return defaultValue || "";
        };
        """
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": alert_injection_script})

    def process_ws_events(self):
        ws_messages = self.driver.execute_script("""
            var messagesCopy = {};
            for (var id in window.myWsMessages) {
                messagesCopy[id] = window.myWsMessages[id].slice();
                window.myWsMessages[id] = [];
            }
            return messagesCopy;
        """)
        for msg_key, msgs in ws_messages.items():
            for msg in msgs:
                ws_logger.info(f"RECV: ({msg_key}) {msg}")
                if isinstance(msg, list) and len(msg) >= 2:
                    event_type, event_details = msg[0], msg[1]
                    event_key = f"ws_{event_type}"
                    if event_key in self.event_handlers:
                        self.event_handlers[event_key](event_details)
                    elif event_key == "ws_you":
                        self.my_id = event_details
        return

    def send_ws_message(self, contents: list):
        ws_logger.info(f"SEND: {contents}")
        ws_ids = self.driver.execute_script("return Object.keys(window.myWebSockets);")
        if not ws_ids:
            print("no websocket")
            return
        ws_id = ws_ids[-1]
        # Only send if on a group page
        if not self.driver.current_url.startswith("https://tagpro.koalabeast.com/groups/"):
            return
        group_id = self.driver.current_url.strip('/').split('/')[-1]
        message = f'42/groups/{group_id},{json.dumps(contents)}'
        try:
            self.driver.execute_script(
                """
                var ws = window.myWebSockets[arguments[0]];
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(arguments[1]);
                } else {
                    console.warn("Cannot send message: WebSocket not found or not open.", ws, ws.readyState);
                }
                """,
                ws_id, message
            )
        except JavascriptException as e:
            event_logger.error(str(e))
            print("TODO: LOOK INTO THIS", e)

    def get_lobby_players(self):
        teams = ["red-team", "blue-team", "spectators", "waiting"]
        lobby_players = {team: self.driver.execute_script(f"""
            return Array.from(document.querySelectorAll("#{team} li.player-item")).map(el => {{
                return {{
                    name: el.querySelector('.player-name') ? el.querySelector('.player-name').innerText : "",
                    location: el.querySelector('.player-location') ? el.querySelector('.player-location').innerText : ""
                }};
            }});
        """) for team in teams}
        return lobby_players

    def find_elements(self, css_selector: str):
        return self.driver.find_elements(By.CSS_SELECTOR, css_selector)

    def is_game_active(self):
        """Return True if the join-game button is displayed."""
        join_game_btns = self.find_elements("#join-game-btn")
        return any(b.is_displayed() for b in join_game_btns)

    def send_chat_msg(self, text: str):
        for line in text.split("\n"):
            self.send_ws_message(["chat", line])


class TagproBot:
    URL = "https://tagpro.koalabeast.com/groups/"
    room_name = "Tryhard Gravity Lobby"
    default_map_settings = {"category": None, "difficulty": (1.0, 3.5), "minfun": 3.0}
    default_lobby_settings = {"region": "US Central"}
    moderator_names = ["FWO", "DAD.", "TeaForYou&Me", "Some Ball 64", "MRCOW", "Billy", "hmmmm", "Valerian", "3"]
    restricted_names = ["Fap", "Ptuh", "marvin"]
    region_map = {"east": "US East", "central": "US Central", "west": "US West", "eu": "Europe", "oce": "Oceanic", "oceanic": "Oceanic"}

    def __init__(self, adapter: DriverAdapter):
        self.adapter = adapter
        self.settings = dict(self.default_map_settings)
        self.lobby_settings = dict(self.default_lobby_settings)

        self.authed_members = {}

        ####
        # STATE
        self.lobby_players = None
        self.finding_game_start_time = None
        self.current_preset = None
        self.current_game_preset = None
        self.current_game_uuid = None
        self.game_is_active = False
        ###

        self.adapter.event_handlers["ws_chat"] = self.handle_chat
        self.adapter.event_handlers["ws_member"] = self.handle_member
        self.adapter.event_handlers["ws_removed"] = self.handle_team_change
        self.adapter.event_handlers["ws_game"] = self.handle_game

        self.disallow_someballs = False

    @property
    def game_str(self):
        if self.current_game_preset is None:
            return "No current game preset set."
        curr_maps = [m for m in get_maps() if m["preset"] == self.current_game_preset]
        if not curr_maps:
            return f"Sorry, I don't know the MAP details for {self.current_game_preset}"
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

    @property
    def num_ready_balls(self):
        self.adapter.send_chat_msg(f"Lobby Players: {self.lobby_players}")
        if self.lobby_players is None:
            return 0
        return len(self.lobby_players["red-team"])

    @property
    def num_in_lobby(self):
        return sum(len(v) for v in self.lobby_players.values())

    def ensure_in_group(self, room_name):
        """Ensures the browser is in the desired group by room name."""
        current_url = self.adapter.driver.current_url

        if current_url == "https://tagpro.koalabeast.com/games/find":
            if self.finding_game_start_time is None:
                self.finding_game_start_time = time.time()
            time_waiting = time.time() - self.finding_game_start_time
            if time_waiting > 300:  # Wait 5 minutes before giving up
                print(f"Stuck finding game for {time_waiting:.1f} seconds, creating new group")
                self.adapter.driver.get("https://tagpro.koalabeast.com/groups/")
                return
            print(f"Finding game... waiting {time_waiting:.1f} seconds")
            return
        self.finding_game_start_time = None 

        if current_url == "https://tagpro.koalabeast.com/groups/":
            group_items = self.adapter.find_elements("div.group-item")
            for group in group_items:
                if group.find_element(By.CSS_SELECTOR, ".group-name").text.strip() == room_name:
                    join_button = group.find_element(By.CSS_SELECTOR, "a.btn.btn-primary.pull-right")
                    join_button.click()
                    time.sleep(1)
                    return True
            else:
                # create group
                create_btns = self.adapter.find_elements("#create-group-btn")
                if create_btns:
                    create_btns[0].click()

        elif not current_url.startswith("https://tagpro.koalabeast.com/groups/"):
            if current_url == "https://tagpro.koalabeast.com/game":
                for _ in range(5):
                    client_info = self.adapter.driver.execute_script("return tagpro.clientInfo;")
                    if client_info is not None:
                        self.current_game_uuid = client_info["gameUuid"]
                        event_logger.info(f"Game UUID: {self.current_game_uuid}")
                        write_replay_uuid(self.current_game_uuid)
                        break
                    time.sleep(1)
                else:
                    print("FAILED TO GET CLIENTINFO")

            self.adapter.driver.get("https://tagpro.koalabeast.com/groups/")

        else:  # currently in group, ensure sane state
            self.adapter.send_ws_message(["setting", {"name": "groupName", "value": room_name}])
            self.adapter.send_ws_message(["setting", {"name": "serverSelect", "value": "false"}])
            self.adapter.send_ws_message(["setting", {"name": "regions", "value": self.lobby_settings["region"]}])
            self.adapter.send_ws_message(["setting", {"name": "discoverable", "value": "true"}])
            self.adapter.send_ws_message(["setting", {"name": "redTeamName", "value": "Good Team"}])
            self.adapter.send_ws_message(["setting", {"name": "blueTeamName", "value": "Bad Team"}])
            self.adapter.send_ws_message(["setting", {"name": "ghostMode", "value": "noPlayerOrMarsCollisions"}])
            
            if self.adapter.my_id is not None:
                self.adapter.send_ws_message(["team", {"id": self.adapter.my_id, "team": 3}])
            try:
                if any([b.is_displayed() for b in self.adapter.find_elements("#pug-btn")]):
                    self.adapter.send_ws_message(["pug"])
                    self.adapter.send_ws_message(["setting", {"name": "isPrivate", "value": "true"}])
            except Exception as e:
                print("FAILED HERE")
                print("----")
                print(e)
                print("----")

    def handle_game(self, event_details):
        if event_details.get("gameId") is None:
            # Don't immediately end the game - give it time to load
            if self.game_is_active:
                # Start a timer for ending the game
                if not hasattr(self, 'game_end_timer_start'):
                    self.game_end_timer_start = time.time()
                    event_logger.info("GameId is None, starting end game timer")
                elif time.time() - self.game_end_timer_start > 10:  # Wait 10 seconds
                    # Game has been without gameId for 10 seconds, end it
                    event_logger.info(f"End of game: {self.current_game_preset}")
                    self.game_is_active = False
                    self.adapter.send_chat_msg("GG. Loading next map. Please return to lobby.")
                    delattr(self, 'game_end_timer_start')
            else:
                # Game wasn't active, so this is just normal loading
                pass
        else:
            # Game has a gameId, reset the end timer and ensure game is active
            if hasattr(self, 'game_end_timer_start'):
                delattr(self, 'game_end_timer_start')
                
            event_logger.info(f"Game Running: {self.current_game_preset}")
            
            # Only set game as active if there are actually players ready
            if not self.game_is_active and self.num_ready_balls > 0:
                self.game_is_active = True
                event_logger.info(f"Game activated with {self.num_ready_balls} ready players")
            elif self.game_is_active and self.num_ready_balls == 0:
                # If game was active but no players are ready, keep it active for a bit
                # This prevents immediate game ending when players are still joining
                pass
            
            # Delay the ensure_in_group call to let joiner phase complete
            # This prevents the bot from immediately leaving the game during startup
            if not hasattr(self, 'delayed_group_check'):
                self.delayed_group_check = time.time()
                event_logger.info("Game started, will check group state after joiner phase...")
                # Schedule the group check for later instead of doing it immediately
                import threading
                def delayed_group_check():
                    time.sleep(15)  # Wait 15 seconds for joiner phase
                    event_logger.info("Joiner phase should be complete, checking group state...")
                    self.ensure_in_group(self.room_name)
                    if hasattr(self, 'delayed_group_check'):
                        delattr(self, 'delayed_group_check')
                
                threading.Thread(target=delayed_group_check, daemon=True).start()

    def handle_member(self, event_details):
        if event_details.get("auth") and event_details.get("name"):
            self.authed_members[event_details["name"]] = event_details["id"]
        elif self.disallow_someballs:
            self.adapter.send_ws_message(["kick", event_details["id"]])
        self.handle_team_change(event_details)

    def handle_team_change(self, _):
        lobby_players = self.adapter.get_lobby_players()

        if lobby_players == self.lobby_players:
            return

        self.lobby_players = lobby_players
        event_logger.info(f"(Red) Ready balls: {self.num_ready_balls}")
        event_logger.info(f"Lobby Players: {lobby_players}")
        event_logger.info(f"Game active: {self.game_is_active}, Ready players: {self.num_ready_balls}")

        # reset to default if no users
        if self.num_in_lobby == 1:
            self.settings = dict(self.default_map_settings)
            event_logger.info("Empty lobby, reverting to default settings.")
            
        # Auto-assign players to red team if they're in waiting/spectators and we have room
        if self.num_ready_balls < 4:  # Only auto-assign if we have room
            waiting_players = lobby_players.get("waiting", [])
            spectator_players = lobby_players.get("spectators", [])
            
            for player in waiting_players + spectator_players:
                if player.get("name") and player.get("name") != "Some Ball":
                    # Try to find their ID from authed_members
                    player_id = None
                    for name, pid in self.authed_members.items():
                        if name == player["name"]:
                            player_id = pid
                            break
                    
                    if player_id:
                        # Move them to red team
                        self.adapter.send_ws_message(["team", {"id": player_id, "team": 1}])
                        event_logger.info(f"Auto-assigned {player['name']} to red team")
                        break  # Only move one player at a time to avoid spam

    def handle_chat(self, event_details):
        msg = event_details.get("message", "")
        if msg in [
            "Please move some or all players to one of the teams and try again.",
            "All of the players are in the Waiting or Spectators area."
        ]:
            return
        event_logger.info("Chat: " + str(event_details))
        if event_details.get("from") is None and "has joined the group" in msg:
            # determine if the player who joined is logged in
            time.sleep(1)
            self.adapter.send_chat_msg("Welcome!\nJoin the Good Team and click 'Join Game'")
        elif "message" in event_details:
            sender = event_details["from"]

            if event_details.get("auth") and sender in self.restricted_names:
                if msg.strip().startswith("LAUNCHNEW"):
                    return

            if msg.strip() == "HELP":
                self.adapter.send_chat_msg(
                    "Commands: HELP, SETTINGS, MAP, INFO <query>, LAUNCHNEW <preset> (<map_id>), "
                    "REGION east/central/west/eu/oce"
                )
            elif msg.strip() == "PLAY":
                self.adapter.send_ws_message(["team", {"id": self.adapter.my_id, "team": 3}])
            elif msg.strip() == "ALLOW SOMEBALLS":
                self.disallow_someballs = False
                self.adapter.send_chat_msg("SomeBalls are now allowed to play with this group.")
            elif msg.strip() == "BAN SOMEBALLS":
                self.disallow_someballs = True
                self.adapter.send_chat_msg("SomeBalls are now banned from playing with this group.")
                self.adapter.send_chat_msg("Type 'ALLOW SOMEBALLS' to reallow them.")
            elif msg.startswith("LAUNCHNEW"):
                if event_details.get("auth") and (sender in self.authed_members) and (sender in self.moderator_names):
                    preset = None
                    if len(msg.split()) == 2:
                        preset = msg.split()[-1]
                    elif len(msg.split()) == 3 and default_float(msg.split()[2]):
                        preset = inject_map_id_into_preset(msg.split()[1], msg.split()[2])
                    if preset and preset.startswith("gZ"):
                        self.adapter.send_chat_msg("Ending current game...")
                        time.sleep(2)
                        self.adapter.send_ws_message(["endGame"])
                        self.load_preset(preset)
                        time.sleep(2)
                        self.maybe_launch()
                else:
                    self.adapter.send_chat_msg("Only group admins can launch new games. Please ask an admin to do this for you.")
                    return

            elif msg.startswith("SETTINGS"):
                self.handle_settings(msg)
                self.load_random_preset()
            elif msg == "MAP":
                self.adapter.send_chat_msg(self.game_str)
            elif msg.startswith("INFO"):
                if len(msg.strip().split()) > 1:
                    query = msg.strip().split(" ", 1)[1]
                    random.shuffle(PERIODIC_MESSAGES)
                    best_info_str = max(PERIODIC_MESSAGES, key=lambda s: fuzz.partial_ratio(query.lower(), s.lower()))
                    self.adapter.send_chat_msg(best_info_str)
                else:
                    self.adapter.send_chat_msg(random.choice(PERIODIC_MESSAGES))
            elif msg == "MODERATE":
                if event_details["auth"] and sender in self.moderator_names and sender in self.authed_members:
                    self.adapter.send_ws_message(["leader", self.authed_members[event_details["from"]]])
                    self.adapter.send_chat_msg(
                        f"Giving {sender} temporary leader. This is strictly for moderation, not room management."
                        "\nPerform any necessary actions then immediately give leader back to the bot.")
                else:
                    self.adapter.send_chat_msg("Not authorized")
            elif msg.startswith("REGION"):
                region_str = msg.split("REGION", 1)[1].strip().lower()
                if region_str in self.region_map.keys():
                    self.lobby_settings["region"] = self.region_map[region_str]
                    self.adapter.send_chat_msg("Updated region.")
                elif region_str in self.region_map.values():
                    self.lobby_settings["region"] = region_str
                    self.adapter.send_chat_msg("Updated region.")
                else:
                    self.adapter.send_chat_msg("Invalid region selection")

    def handle_settings(self, msg):
        parts = msg.strip().split()
        if msg.strip() == "SETTINGS":
            self.adapter.send_chat_msg("Current settings: " + str(self.settings))
            self.adapter.send_chat_msg("Update settings via SETTINGS <key> <value>")
        elif msg.strip().lower() == "SETTINGS DEFAULT".lower():
            self.settings = dict(self.default_map_settings)
            self.adapter.send_chat_msg("Default settings applied")
        elif len(parts) not in (3, 4) or parts[1].lower() not in self.settings:
            self.adapter.send_chat_msg("Invalid command")
        else:
            key = parts[1]
            value = parts[2] if len(parts) == 3 else parts[2:]
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            if isinstance(value, str) and value.lower() in ("none", "any"):
                value = None
            new_settings = dict(self.settings)
            new_settings[key] = value
            try:
                legal_maps = self.get_legal_maps(get_maps(), new_settings)
            except Exception as e:
                print("FAILED LEGAL MAPS", e)
                legal_maps = None
            if not legal_maps:
                self.adapter.send_chat_msg(f"No maps legal with settings: {new_settings}")
            else:
                self.settings = new_settings
                self.adapter.send_chat_msg(f"Updated settings to: {self.settings}")
                self.adapter.send_chat_msg(f"{len(legal_maps)} legal maps with these settings")

    def maybe_launch(self):
        if self.adapter.is_game_active() or not self.num_ready_balls or self.current_preset is None:
            # When game is inactive, reset all settings
            self.settings = dict(self.default_map_settings)
            self.lobby_settings = dict(self.default_lobby_settings)
            
            return False
        self.current_game_preset = self.current_preset
        self.current_preset = None
        self.adapter.send_ws_message(["groupPlay"])
        event_logger.info(f"Launched preset: {self.current_game_preset}")
        event_logger.info("Waiting for game to load and players to join...")
        time.sleep(5)
        return True

    def get_legal_maps(self, maps, settings):
        if settings["category"]:
            maps = [m for m in maps if settings["category"].lower() in m["category"].lower()]
        if settings["difficulty"]:
            low, high = float(settings["difficulty"][0] or 0.0), float(settings["difficulty"][1] or 100.0)
            maps = [m for m in maps if low <= default_float(m["difficulty"], 10) <= high]
        minfun = default_float(settings["minfun"], 0.0)
        maps = [m for m in maps if default_float(m["fun"], 100) >= minfun]
        maps = [m for m in maps if any(str(br) in m["balls_req"] for br in range((self.num_ready_balls or 1) + 1))]
        return maps

    def load_random_preset(self):
        maps = self.get_legal_maps(get_maps(), self.settings)
        if not maps:
            self.settings = dict(self.default_map_settings)
            maps = self.get_legal_maps(get_maps(), self.settings)
        self.load_preset(random.choice([m["preset"] for m in maps]))

    def load_preset(self, preset):
        self.adapter.send_ws_message(["groupPresetApply", preset])
        self.current_preset = preset
        event_logger.info(f"Set preset: {preset}")

    def run(self):
        i = 1
        launched_new = False
        while True:
            time.sleep(1)

            self.ensure_in_group(self.room_name)
            self.adapter.process_ws_events()

            if launched_new:
                time.sleep(10)
                try:
                    self.adapter.send_chat_msg(self.game_str)
                except Exception as e:
                    print("FAILED TO SEND CHAT MSG", e)
                launched_new = False

            if i % 1800 == 0:
                self.adapter.send_chat_msg(random.choice(PERIODIC_MESSAGES))

            # ensure random preset loaded before launching
            if i % 10 == 0 and not self.adapter.is_game_active() and self.num_in_lobby != 1:
                self.load_random_preset()
                time.sleep(5)
                launched_new = self.maybe_launch()

            i += 1


if __name__ == '__main__':
    adapter = DriverAdapter()
    bot = TagproBot(adapter)
    bot.run()

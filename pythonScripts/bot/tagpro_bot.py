import time
import random
import requests
from selenium.webdriver.common.by import By
from driver_adapter import DriverAdapter
from settings_manager import SettingsManager
from chat_handler import ChatHandler
from utils import setup_logger, get_game_info
from constants import (
    ROOM_NAME, GROUPS_URL, GAME_URL, GROUP_SETTINGS, PERIODIC_MESSAGES,
    FINDING_GAME_TIMEOUT, GAME_END_TIMEOUT, PERIODIC_MESSAGE_INTERVAL,
    PRESET_LOAD_INTERVAL, LAUNCH_DELAY, GAME_STR_DELAY
)
from replay_manager import write_replay_uuid, get_replay_data, get_details


# Create event logger
event_logger = setup_logger("events_logger", "events.txt")


class TagproBot:
    """Main TagPro bot class that manages the game lobby and coordinates all components."""
    
    def __init__(self, adapter: DriverAdapter):
        self.adapter = adapter
        self.settings_manager = SettingsManager()
        self.chat_handler = ChatHandler(adapter, self.settings_manager, self)
        
        # Game state
        self.lobby_players = None
        self.finding_game_start_time = None
        self.current_preset = None
        self.current_game_preset = None
        self.current_game_uuid = None
        self.game_is_active = False
        self.game_id_pending = False
        self.group_configured = False

        # Set up event handlers
        self.adapter.event_handlers["ws_chat"] = self.chat_handler.handle_chat
        self.adapter.event_handlers["ws_member"] = self.chat_handler.handle_member
        self.adapter.event_handlers["ws_removed"] = self.handle_team_change
        self.adapter.event_handlers["ws_game"] = self.handle_game

    @property
    def game_str(self):
        """Get formatted game information string."""
        return get_game_info(self.current_game_preset)

    @property
    def num_ready_balls(self):
        """Get number of ready players."""
        if self.lobby_players is None:
            print(f"DEBUG: lobby_players is None")
            return 0
        # Use .get to avoid KeyError if snapshot is malformed or incomplete
        red_team_count = len(self.lobby_players.get("red-team", []))
        print(f"DEBUG: num_ready_balls calculation: lobby_players={self.lobby_players}, red_team_count={red_team_count}")
        return red_team_count

    @property
    def num_in_lobby(self):
        """Get total number of players in lobby."""
        if self.lobby_players is None:
            return 0
        return sum(len(v) for v in self.lobby_players.values())

    def ensure_in_group(self, room_name):
        """Ensure the browser is in the desired group."""
        current_url = self.adapter.driver.current_url
        
        print(f"DEBUG: ensure_in_group called. Current URL: {current_url}, room_name: {room_name}")

        # If game ID is pending, don't navigate away from game page
        if self.game_id_pending and current_url == GAME_URL:
            event_logger.info("Game ID pending, staying in game during joiner phase")
            return

        # Handle finding game state
        if current_url == "https://tagpro.koalabeast.com/games/find":
            if self.finding_game_start_time is None:
                self.finding_game_start_time = time.time()
            
            time_waiting = time.time() - self.finding_game_start_time
            if time_waiting > FINDING_GAME_TIMEOUT:
                print(f"Stuck finding game for {time_waiting:.1f} seconds, creating new group")
                self.adapter.driver.get(GROUPS_URL)
                return
            
            print(f"Finding game... waiting {time_waiting:.1f} seconds")
            return
        
        self.finding_game_start_time = None

        # Handle groups page
        if current_url == GROUPS_URL:
            group_items = self.adapter.find_elements("div.group-item")
            for group in group_items:
                if group.find_element(By.CSS_SELECTOR, ".group-name").text.strip() == room_name:
                    join_button = group.find_element(By.CSS_SELECTOR, "a.btn.btn-primary.pull-right")
                    join_button.click()
                    time.sleep(1)
                    return True
            else:
                # Create group if not found
                create_btns = self.adapter.find_elements("#create-group-btn")
                if create_btns:
                    create_btns[0].click()

        # Handle other pages
        elif not current_url.startswith(GROUPS_URL):
            if current_url == GAME_URL:
                self._handle_game_page()
            
            self.adapter.driver.get(GROUPS_URL)
            self.group_configured = False  # Reset flag when leaving group

        # Handle group configuration
        else:
            print(f"DEBUG: In group configuration section. group_configured = {self.group_configured}")
            
            # Only configure once, since the server confirms settings are applied
            if not self.group_configured:
                print("DEBUG: Calling _configure_group()")
                self._configure_group()
                self.group_configured = True
                print("DEBUG: Set group_configured = True")
            else:
                print("DEBUG: Group already configured, skipping configuration")

    def ensure_group_session(self):
        """Health check to ensure we are in a group; join or create if needed.
        - If at game and in joiner phase, stay.
        - If not on groups page, navigate there.
        - If on groups page, attempt join; if not found, create; then configure and move to spectators.
        """
        current_url = self.adapter.driver.current_url
        # Do not navigate or reconfigure during joiner/game start phase
        if self.game_id_pending:
            return

        if not current_url.startswith(GROUPS_URL):
            self.adapter.driver.get(GROUPS_URL)
            self.group_configured = False
            return

        # On groups page: try to join or create
        if not self._try_join_group_by_name(ROOM_NAME):
            self._create_group()

    def _try_join_group_by_name(self, room_name):
        """Return True if joined target group, False otherwise."""
        group_items = self.adapter.find_elements("div.group-item")
        for group in group_items:
            try:
                name_text = group.find_element(By.CSS_SELECTOR, ".group-name").text.strip()
            except Exception:
                continue
            if name_text == room_name:
                try:
                    join_button = group.find_element(By.CSS_SELECTOR, "a.btn.btn-primary.pull-right")
                    join_button.click()
                    time.sleep(1)
                    self._post_join_or_create_setup()
                    return True
                except Exception:
                    return False
        return False

    def _create_group(self):
        """Create a new group and run setup."""
        create_btns = self.adapter.find_elements("#create-group-btn")
        if create_btns:
            try:
                create_btns[0].click()
                time.sleep(1)
            except Exception:
                return False
        self._post_join_or_create_setup()
        return True

    def _post_join_or_create_setup(self):
        """After joining/creating: configure settings, ensure public if desired, move to spectators."""
        # Avoid reconfiguring during joiner to prevent race with game start
        if not self.group_configured and not self.game_id_pending and not self.adapter.is_game_active():
            self._configure_group()
            self.group_configured = True
        # Move to spectators when we know our id
        if self.adapter.my_id is not None:
            self.adapter.send_ws_message(["team", {"id": self.adapter.my_id, "team": 3}])

    def _handle_game_page(self):
        """Handle being on the game page."""
        game_uuid = self.adapter.get_game_uuid()
        if game_uuid:
            self.current_game_uuid = game_uuid
            event_logger.info(f"Game UUID: {self.current_game_uuid}")
            # Don't write UUID to file yet - wait until game ends
        else:
            print("FAILED TO GET CLIENTINFO")

    def _configure_group(self):
        """Configure group settings."""
        lobby_settings = self.settings_manager.get_lobby_settings()
        
        event_logger.info("Configuring group settings...")
        print("DEBUG: Configuring group settings...")
        
        # Set group name and basic settings
        for setting_name, setting_value in GROUP_SETTINGS.items():
            event_logger.info(f"Sending group setting: {setting_name} = {setting_value}")
            print(f"DEBUG: Sending group setting: {setting_name} = {setting_value}")
            self.adapter.send_ws_message(["setting", {"name": setting_name, "value": setting_value}])
        
        # Move bot to spectators
        if self.adapter.my_id is not None:
            self.adapter.send_ws_message(["team", {"id": self.adapter.my_id, "team": 3}])
        
        # Handle PUG mode
        try:
            pug_btns = self.adapter.find_elements("#pug-btn")
            if any([b.is_displayed() for b in pug_btns]):
                self.adapter.send_ws_message(["pug"])
                self.adapter.send_ws_message(["setting", {"name": "isPrivate", "value": "true"}])
        except Exception as e:
            print("FAILED HERE")
            print("----")
            print(e)
            print("----")

    def handle_game(self, event_details):
        """Handle game events."""
        if event_details.get("gameId") is None:
            # Game ID is None - this could be game starting or ending
            if self.game_id_pending:
                # We're waiting for game ID, this is normal startup
                event_logger.info("Game starting, waiting for game ID...")
                return
            elif self.game_is_active:
                # Game was active but now has no ID, start end timer
                if not hasattr(self, 'game_end_timer_start'):
                    self.game_end_timer_start = time.time()
                    event_logger.info("GameId is None, starting end game timer")
                elif time.time() - self.game_end_timer_start > GAME_END_TIMEOUT:
                    # Game has been without gameId for timeout period, end it
                    event_logger.info(f"End of game: {self.current_game_preset}")
                    
                    # Process and upload replay if we have a UUID
                    if hasattr(self, 'current_game_uuid') and self.current_game_uuid:
                        self._process_and_upload_replay(self.current_game_uuid)
                    
                    self.game_is_active = False
                    self.game_id_pending = False
                    self.adapter.send_chat_msg("GG. Loading next map. Please return to lobby.")
                    delattr(self, 'game_end_timer_start')
        else:
            # Game has a gameId - game is now fully started
            if hasattr(self, 'game_end_timer_start'):
                delattr(self, 'game_end_timer_start')
            
            # Clear pending state since we now have a game ID
            if self.game_id_pending:
                self.game_id_pending = False
                event_logger.info(f"Game ID received: {event_details.get('gameId')}, joiner phase complete")
                # Reset current_preset to None since game has actually started
                self.current_preset = None
                
            event_logger.info(f"Game Running: {self.current_game_preset}")
            
            # Only set game as active if there are actually players ready
            if not self.game_is_active and self.num_ready_balls > 0:
                self.game_is_active = True
                event_logger.info(f"Game activated with {self.num_ready_balls} ready players")

    def handle_team_change(self, lobby_snapshot=None):
        """Handle lobby/team changes and keep ready counts in sync.

        This is invoked in two ways:
        - From DOM polling (e.g., ws_removed handler) with no snapshot provided
        - From ws_member events (chat handler) passing a fresh snapshot

        We normalize snapshots to avoid false negatives due to ordering and
        only log when a real change occurs.
        """
        # Obtain a fresh snapshot if one was not provided or looks invalid
        expected_teams = {"red-team", "blue-team", "spectators", "waiting"}
        snapshot_is_valid = isinstance(lobby_snapshot, dict) and any(
            key in expected_teams for key in lobby_snapshot.keys()
        )
        lobby_players_current = (
            lobby_snapshot if snapshot_is_valid else self.adapter.get_lobby_players()
        )

        # Normalize snapshots for robust comparison (order-insensitive)
        def _normalize(snapshot):
            normalized = {}
            for team_name, players in (snapshot or {}).items():
                player_tuples = []
                for p in players:
                    if isinstance(p, dict):
                        player_tuples.append((p.get("name", ""), p.get("location", "")))
                    else:
                        # Handle case where player is a string or other type
                        player_tuples.append((str(p), ""))
                normalized[team_name] = sorted(player_tuples)
            return normalized

        current_norm = _normalize(lobby_players_current)
        previous_norm = _normalize(self.lobby_players)

        if current_norm == previous_norm:
            # No material change; avoid noisy logs
            return

        # Commit the new snapshot and log concise state
        self.lobby_players = lobby_players_current
        red_count = self.num_ready_balls
        print(f"(Red) Ready balls: {red_count}")
        print(f"Lobby Players: {self.lobby_players}")
        print(
            f"Game active: {self.game_is_active}, Ready players: {red_count}"
        )

        # Only reset to default if no users AND we haven't set custom settings
        if self.num_in_lobby == 1:
            # Preserve custom settings - don't reset them when lobby becomes empty
            event_logger.info("Empty lobby, preserving current settings.")
            self.game_id_pending = False  # Reset pending state if lobby is empty

    def maybe_launch(self):
        """Attempt to launch a game if conditions are met."""
        if self.adapter.is_game_active() or not self.num_ready_balls or self.current_preset is None:
            return False
        
        self.current_game_preset = self.current_preset
        # Don't set current_preset to None immediately - keep it for potential re-launches
        self.game_id_pending = True  # Set pending state before launching
        print(f"DEBUG: maybe_launch: preset={self.current_game_preset} ready_balls={self.num_ready_balls} url={self.adapter.driver.current_url}")
        self.adapter.send_ws_message(["groupPlay"])
        event_logger.info(f"Launched preset: {self.current_game_preset}")
        event_logger.info("Game ID pending - bot will stay in game during joiner phase")
        time.sleep(LAUNCH_DELAY)
        return True

    def load_random_preset(self):
        """Load a random preset based on current settings."""
        preset = self.settings_manager.get_random_preset(self.num_ready_balls)
        self.load_preset(preset)

    def load_preset(self, preset):
        """Load a specific preset."""
        self.adapter.send_ws_message(["groupPresetApply", preset])
        self.current_preset = preset
        event_logger.info(f"Set preset: {preset}")
        # Give the preset time to apply
        time.sleep(2)

    def _process_and_upload_replay(self, game_uuid):
        """Process a replay and upload it to the world records site."""
        try:
            event_logger.info(f"Processing replay for UUID: {game_uuid}")
            
            # Get replay data from TagPro
            replay_data = get_replay_data(game_uuid)
            if not replay_data:
                event_logger.info(f"Failed to get replay data for UUID: {game_uuid}")
                return
            
            # Extract world record details using existing function
            replay_details = get_details(replay_data)
            if not replay_details or replay_details.get("record_time") is None:
                event_logger.info(f"No valid world record data for UUID: {game_uuid}")
                return
            
            # Filter to only include maps in spreadsheet (same logic as replay_manager)
            from maps import get_maps
            spreadsheet_map_ids = set([m["map_id"] for m in get_maps()])
            
            if replay_details["map_id"] not in spreadsheet_map_ids:
                event_logger.info(f"Map {replay_details['map_id']} not in spreadsheet, skipping upload")
                return
            
            # Upload single replay to world records site
            response = requests.post(
                "https://worldrecords.bambitp.workers.dev/upload",
                params={"password": "insertPW"},
                headers={"Content-Type": "application/json"},
                json=[replay_details],
                timeout=30
            )
            
            if response.status_code == 200:
                event_logger.info(f"Successfully uploaded replay to world records site: {game_uuid}")
                event_logger.info(f"Record: {replay_details['record_time']}ms by {replay_details['capping_player']} on {replay_details['map_name']}")
                
                # Only save UUID to file after successful upload
                write_replay_uuid(game_uuid)
                event_logger.info(f"Saved UUID to replay_uuids.txt: {game_uuid}")
            else:
                event_logger.info(f"Failed to upload replay. Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            event_logger.info(f"Error processing replay {game_uuid}: {e}")
            # Don't let replay processing errors crash the bot

    def run(self):
        """Main bot loop."""
        i = 1
        launched_new = False
        
        while True:
            time.sleep(1)

            self.adapter.process_ws_events()

            if self.game_id_pending:
                dbg = self.adapter.get_ws_debug_info()
                print(f"DEBUG: joiner phase active. url={dbg['url']} on_groups={dbg['on_groups']} ws_ids={dbg['ws_ids']} readyState={dbg['last_ready_state']}")

            # Health check: ensure we are in a specific group page; if not, navigate and join/create
            self.ensure_group_session()

            if launched_new:
                print("LAUNCHED NEW")
                time.sleep(GAME_STR_DELAY)
                try:
                    dbg = self.adapter.get_ws_debug_info()
                    print(f"DEBUG: sending game_str. url={dbg['url']} on_groups={dbg['on_groups']} ws_ids={dbg['ws_ids']} readyState={dbg['last_ready_state']}")
                    self.adapter.send_chat_msg(self.game_str)
                except Exception as e:
                    print("FAILED TO SEND CHAT MSG", e)
                launched_new = False

            # Send periodic messages
            if i % PERIODIC_MESSAGE_INTERVAL == 0:
                self.adapter.send_chat_msg(random.choice(PERIODIC_MESSAGES))

            # Load random preset and maybe launch
            if i % PRESET_LOAD_INTERVAL == 0 and not self.adapter.is_game_active() and self.num_in_lobby != 1:
                event_logger.info(f"Attempting to load preset and launch: i={i}, is_game_active={self.adapter.is_game_active()}, num_in_lobby={self.num_in_lobby}")
                print(f"DEBUG: Attempting to load preset and launch: i={i}, is_game_active={self.adapter.is_game_active()}, num_in_lobby={self.num_in_lobby}")
                self.load_random_preset()
                # Give time for preset to load before trying to launch
                time.sleep(LAUNCH_DELAY)
                # Try to launch if conditions are met
                launched_new = self.maybe_launch()
                if launched_new:
                    print(f"DEBUG: Successfully launched game with preset: {self.current_game_preset}")
                else:
                    print(f"DEBUG: Failed to launch game. Conditions: is_game_active={self.adapter.is_game_active()}, num_ready_balls={self.num_ready_balls}, current_preset={self.current_preset}")

            # (Deprecated) Periodic ensure_in_group replaced by continuous health check
            
            i += 1

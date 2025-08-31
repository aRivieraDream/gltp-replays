import time
import random
from selenium.webdriver.common.by import By
from driver_adapter import DriverAdapter
from settings_manager import SettingsManager
from chat_handler import ChatHandler
from utils import setup_logger, get_game_info
from constants import (
    ROOM_NAME, GROUPS_URL, GAME_URL, PERIODIC_MESSAGES,
    FINDING_GAME_TIMEOUT, GAME_END_TIMEOUT, PERIODIC_MESSAGE_INTERVAL,
    PRESET_LOAD_INTERVAL, LAUNCH_DELAY, GAME_STR_DELAY
)
from replay_manager import write_replay_uuid


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
            return 0
        return len(self.lobby_players["red-team"])

    @property
    def num_in_lobby(self):
        """Get total number of players in lobby."""
        if self.lobby_players is None:
            return 0
        return sum(len(v) for v in self.lobby_players.values())

    def ensure_in_group(self, room_name):
        """Ensure the browser is in the desired group."""
        current_url = self.adapter.driver.current_url

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

        # Handle group configuration
        else:
            self._configure_group()

    def _handle_game_page(self):
        """Handle being on the game page."""
        game_uuid = self.adapter.get_game_uuid()
        if game_uuid:
            self.current_game_uuid = game_uuid
            event_logger.info(f"Game UUID: {self.current_game_uuid}")
            write_replay_uuid(self.current_game_uuid)
        else:
            print("FAILED TO GET CLIENTINFO")

    def _configure_group(self):
        """Configure group settings."""
        lobby_settings = self.settings_manager.get_lobby_settings()
        
        # Set group name and basic settings
        self.adapter.send_ws_message(["setting", {"name": "groupName", "value": ROOM_NAME}])
        self.adapter.send_ws_message(["setting", {"name": "serverSelect", "value": "false"}])
        self.adapter.send_ws_message(["setting", {"name": "regions", "value": lobby_settings["region"]}])
        self.adapter.send_ws_message(["setting", {"name": "discoverable", "value": "true"}])
        self.adapter.send_ws_message(["setting", {"name": "redTeamName", "value": "Good Team"}])
        self.adapter.send_ws_message(["setting", {"name": "blueTeamName", "value": "Bad Team"}])
        self.adapter.send_ws_message(["setting", {"name": "ghostMode", "value": "noPlayerOrMarsCollisions"}])
        
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
                
            event_logger.info(f"Game Running: {self.current_game_preset}")
            
            # Only set game as active if there are actually players ready
            if not self.game_is_active and self.num_ready_balls > 0:
                self.game_is_active = True
                event_logger.info(f"Game activated with {self.num_ready_balls} ready players")

    def handle_team_change(self, _):
        """Handle team change events."""
        lobby_players = self.adapter.get_lobby_players()

        if lobby_players == self.lobby_players:
            return

        self.lobby_players = lobby_players
        event_logger.info(f"(Red) Ready balls: {self.num_ready_balls}")
        event_logger.info(f"Lobby Players: {lobby_players}")
        event_logger.info(f"Game active: {self.game_is_active}, Ready players: {self.num_ready_balls}")

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
        self.current_preset = None
        self.game_id_pending = True  # Set pending state before launching
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

    def run(self):
        """Main bot loop."""
        i = 1
        launched_new = False
        
        while True:
            time.sleep(1)

            self.adapter.process_ws_events()

            if launched_new:
                print("LAUNCHED NEW")
                time.sleep(GAME_STR_DELAY)
                try:
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
                self.load_random_preset()
                # Give time for preset to load before trying to launch
                time.sleep(LAUNCH_DELAY)
                # Try to launch if conditions are met
                launched_new = self.maybe_launch()

            i += 1
            self.ensure_in_group(ROOM_NAME)

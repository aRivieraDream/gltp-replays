import random
try:
    from rapidfuzz import fuzz
except ImportError:
    # Fallback if rapidfuzz is not available
    def fuzz_partial_ratio(query, target):
        return 0.0 if query.lower() not in target.lower() else 50.0
    fuzz = type('Fuzz', (), {'partial_ratio': fuzz_partial_ratio})()
from maps import inject_map_id_into_preset
from utils import find_best_info_message, get_game_info
from constants import (
    MODERATOR_NAMES, RESTRICTED_NAMES, PERIODIC_MESSAGES, 
    DISCORD_LINK
)


class ChatHandler:
    """Handles chat messages and commands for the TagPro bot."""
    
    def __init__(self, adapter, settings_manager, bot):
        self.adapter = adapter
        self.settings_manager = settings_manager
        self.bot = bot
        self.authed_members = {}
        self.disallow_someballs = False

    def handle_chat(self, event_details):
        """Main chat message handler."""
        msg = event_details.get("message", "")
        
        # Ignore system messages
        if msg in [
            "Please move some or all players to one of the teams and try again.",
            "All of the players are in the Waiting or Spectators area."
        ]:
            return
        
        # Handle join messages
        if event_details.get("from") is None and "has joined the group" in msg:
            self._handle_join_message()
            return
        
        # Handle regular chat messages
        if "message" in event_details:
            sender = event_details["from"]
            self._handle_chat_message(sender, msg, event_details)

    def _handle_join_message(self):
        """Handle when a player joins the group."""
        import time
        time.sleep(1)
        self.adapter.send_chat_msg("Welcome!\nJoin the Good Team and click 'Join Game'")

    def _handle_chat_message(self, sender, msg, event_details):
        """Handle regular chat messages and commands."""
        # Check for restricted names
        if event_details.get("auth") and sender in RESTRICTED_NAMES:
            if msg.strip().startswith("LAUNCHNEW"):
                return
        
        # Process commands
        if msg.strip() == "HELP":
            self._handle_help_command()
        elif msg.strip() == "SAVE":
            self._handle_save_command()
        elif msg.strip() == "PLAY":
            self._handle_play_command()
        elif msg.strip() == "ALLOW SOMEBALLS":
            self._handle_allow_someballs_command()
        elif msg.strip() == "BAN SOMEBALLS":
            self._handle_ban_someballs_command()
        elif msg.startswith("LAUNCHNEW"):
            self._handle_launchnew_command(sender, msg, event_details)
        elif msg.startswith("SETTINGS"):
            self._handle_settings_command(msg)
        elif msg == "MAP":
            self._handle_map_command()
        elif msg.startswith("INFO"):
            self._handle_info_command(msg)
        elif msg == "MODERATE":
            self._handle_moderate_command(sender, event_details)
        elif msg.startswith("REGION"):
            self._handle_region_command(msg)

    def _handle_help_command(self):
        """Handle HELP command."""
        self.adapter.send_chat_msg(
            "Commands: HELP, SETTINGS, MAP, INFO <query>, LAUNCHNEW <preset> (<map_id>), "
            "REGION east/central/west/eu/oce, SAVE"
        )

    def _handle_save_command(self):
        """Handle SAVE command."""
        self.settings_manager.save_current_settings()
        self.adapter.send_chat_msg("Settings saved!")

    def _handle_play_command(self):
        """Handle PLAY command."""
        self.adapter.send_ws_message(["team", {"id": self.adapter.my_id, "team": 3}])

    def _handle_allow_someballs_command(self):
        """Handle ALLOW SOMEBALLS command."""
        self.disallow_someballs = False
        self.adapter.send_chat_msg("SomeBalls are now allowed to play with this group.")

    def _handle_ban_someballs_command(self):
        """Handle BAN SOMEBALLS command."""
        self.disallow_someballs = True
        self.adapter.send_chat_msg("SomeBalls are now banned from playing with this group.")
        self.adapter.send_chat_msg("Type 'ALLOW SOMEBALLS' to reallow them.")

    def _handle_launchnew_command(self, sender, msg, event_details):
        """Handle LAUNCHNEW command."""
        if not (event_details.get("auth") and sender in self.authed_members and sender in MODERATOR_NAMES):
            self.adapter.send_chat_msg("Only group admins can launch new games. Please ask an admin to do this for you.")
            return
        
        preset = None
        if len(msg.split()) == 2:
            preset = msg.split()[-1]
        elif len(msg.split()) == 3:
            from utils import default_float
            if default_float(msg.split()[2]):
                preset = inject_map_id_into_preset(msg.split()[1], msg.split()[2])
        
        if preset and preset.startswith("gZ"):
            self.adapter.send_chat_msg("Ending current game...")
            import time
            time.sleep(2)
            self.adapter.send_ws_message(["endGame"])
            self.bot.game_id_pending = False
            self.bot.load_preset(preset)
            time.sleep(2)
            self.bot.maybe_launch()

    def _handle_settings_command(self, msg):
        """Handle SETTINGS command."""
        response = self.settings_manager.handle_settings_command(msg)
        self.adapter.send_chat_msg(response)
        self.bot.load_random_preset()

    def _handle_map_command(self):
        """Handle MAP command."""
        print(f"DEBUG: MAP command received! current_game_preset: {self.bot.current_game_preset}")
        game_info = get_game_info(self.bot.current_game_preset)
        print(f"DEBUG: game_info result: {game_info}")
        self.adapter.send_chat_msg(game_info)

    def _handle_info_command(self, msg):
        """Handle INFO command."""
        if len(msg.strip().split()) > 1:
            query = msg.strip().split(" ", 1)[1]
            best_info_str = find_best_info_message(query, PERIODIC_MESSAGES)
            self.adapter.send_chat_msg(best_info_str)
        else:
            self.adapter.send_chat_msg(random.choice(PERIODIC_MESSAGES))

    def _handle_moderate_command(self, sender, event_details):
        """Handle MODERATE command."""
        if event_details["auth"] and sender in MODERATOR_NAMES and sender in self.authed_members:
            self.adapter.send_ws_message(["leader", self.authed_members[event_details["from"]]])
            self.adapter.send_chat_msg(
                f"Giving {sender} temporary leader. This is strictly for moderation, not room management.\n"
                "Perform any necessary actions then immediately give leader back to the bot."
            )
        else:
            self.adapter.send_chat_msg("Not authorized")

    def _handle_region_command(self, msg):
        """Handle REGION command."""
        response = self.settings_manager.handle_region_command(msg)
        self.adapter.send_chat_msg(response)

    def handle_member(self, event_details):
        """Handle member join/leave events."""
        if event_details.get("auth") and event_details.get("name"):
            self.authed_members[event_details["name"]] = event_details["id"]
        elif self.disallow_someballs:
            self.adapter.send_ws_message(["kick", event_details["id"]])

    def get_authed_members(self):
        """Get authenticated members."""
        return self.authed_members

    def is_someballs_disallowed(self):
        """Check if SomeBalls are disallowed."""
        return self.disallow_someballs

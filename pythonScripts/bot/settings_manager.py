import random
from maps import get_maps, inject_map_id_into_preset
from utils import get_legal_maps, save_settings, load_settings, default_float
from constants import DEFAULT_MAP_SETTINGS, DEFAULT_LOBBY_SETTINGS, REGION_MAP


class SettingsManager:
    """Manages bot settings and configuration."""
    
    def __init__(self):
        self.settings = self.load_saved_settings()
        self.lobby_settings = dict(DEFAULT_LOBBY_SETTINGS)

    def load_saved_settings(self):
        """Load settings from file, fall back to defaults if file doesn't exist."""
        return load_settings('logs/bot_settings.json', DEFAULT_MAP_SETTINGS)

    def save_current_settings(self):
        """Save current settings to file."""
        return save_settings(self.settings, 'logs/bot_settings.json')

    def reset_to_defaults(self):
        """Reset settings to default values."""
        self.settings = dict(DEFAULT_MAP_SETTINGS)
        self.save_current_settings()
        return self.settings

    def update_settings(self, key, value):
        """Update a specific setting."""
        if key not in self.settings:
            return False, f"Invalid key: {key}. Valid keys: {', '.join(self.settings.keys())}"
        
        # Handle special values
        if isinstance(value, str) and value.lower() in ("none", "any"):
            value = None
        
        # Create new settings dict to test
        new_settings = dict(self.settings)
        new_settings[key] = value
        
        # Test if the new settings are valid
        try:
            legal_maps = get_legal_maps(get_maps(), new_settings, 1)  # Test with 1 player
        except Exception as e:
            return False, f"Error validating settings: {e}"
        
        if not legal_maps:
            return False, f"No maps legal with settings: {new_settings}"
        
        # Apply the new settings
        self.settings = new_settings
        self.save_current_settings()
        return True, f"Updated settings to: {self.settings}"

    def get_legal_maps_for_players(self, num_ready_balls):
        """Get maps that are legal with current settings and player count."""
        return get_legal_maps(get_maps(), self.settings, num_ready_balls)

    def get_random_preset(self, num_ready_balls):
        """Get a random preset that matches current settings."""
        maps = self.get_legal_maps_for_players(num_ready_balls)
        
        if not maps:
            # Try with default settings temporarily
            temp_maps = get_legal_maps(get_maps(), DEFAULT_MAP_SETTINGS, num_ready_balls)
            if temp_maps:
                # Use default settings temporarily but don't overwrite user settings
                return random.choice([m["preset"] for m in temp_maps])
            
            # If still no maps, fall back to defaults permanently
            self.settings = dict(DEFAULT_MAP_SETTINGS)
            self.save_current_settings()
            maps = self.get_legal_maps_for_players(num_ready_balls)
        
        return random.choice([m["preset"] for m in maps])

    def handle_settings_command(self, msg):
        """Handle SETTINGS command from chat."""
        parts = msg.strip().split()
        
        if msg.strip() == "SETTINGS":
            return f"Current settings: {self.settings}\nUpdate settings via SETTINGS <key> <value>\nValid keys: {', '.join(self.settings.keys())}"
        
        elif msg.strip().lower() == "SETTINGS DEFAULT".lower():
            self.reset_to_defaults()
            return "Default settings applied"
        
        elif len(parts) not in (3, 4) or parts[1].lower() not in self.settings:
            return f"Invalid command. Valid keys: {', '.join(self.settings.keys())}"
        
        else:
            key = parts[1]
            value = parts[2] if len(parts) == 3 else parts[2:]
            if isinstance(value, list) and len(value) == 1:
                value = value[0]
            
            success, message = self.update_settings(key, value)
            if success:
                legal_maps = self.get_legal_maps_for_players(1)
                return f"{message}\n{len(legal_maps)} legal maps with these settings"
            else:
                return message

    def handle_region_command(self, msg):
        """Handle REGION command from chat."""
        region_str = msg.split("REGION", 1)[1].strip().lower()
        
        if region_str in REGION_MAP:
            self.lobby_settings["region"] = REGION_MAP[region_str]
            return "Updated region."
        elif region_str in REGION_MAP.values():
            self.lobby_settings["region"] = region_str
            return "Updated region."
        else:
            return "Invalid region selection"

    def get_lobby_settings(self):
        """Get current lobby settings."""
        return self.lobby_settings

    def get_map_settings(self):
        """Get current map settings."""
        return self.settings

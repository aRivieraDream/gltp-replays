import time
import json
import platform
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import JavascriptException

from constants import CHROME_OPTIONS, CHROME_PATHS, GROUPS_URL, GAME_URL
from utils import setup_logger


# Create logger for WebSocket events
ws_logger = setup_logger("ws_logger", "ws.txt")


class DriverAdapter:
    """Handles WebDriver setup and WebSocket communication for TagPro."""
    
    def __init__(self):
        self.driver = self._setup_driver()
        self.my_id = None
        self.event_handlers = {}
        
        self.inject_ws_intercept()
        self.inject_auto_close_alerts()

    def _setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        options = webdriver.ChromeOptions()
        
        # Add all chrome options
        for option in CHROME_OPTIONS:
            options.add_argument(option)
        
        # Disable alerts and popups
        options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})
        options.set_capability("goog:chromeOptions", {"prefs": {"profile.default_content_setting_values.popups": 0}})
        options.set_capability("unhandledPromptBehavior", "dismiss")
        
        # Platform-specific browser paths
        system = platform.system()
        chrome_paths = CHROME_PATHS.get(system, [])
        
        # Try each path until one works
        for path in chrome_paths:
            if os.path.exists(path):
                try:
                    print(f"Trying browser at: {path}")
                    service = Service(executable_path=path)
                    driver = webdriver.Chrome(options=options, service=service)
                    print(f"Successfully started browser from: {path}")
                    return driver
                except Exception as e:
                    print(f"Failed to start browser from {path}: {e}")
                    continue
        
        # If no path worked, try letting Selenium find it automatically
        try:
            print("Trying automatic browser detection...")
            driver = webdriver.Chrome(options=options)
            print("Successfully started browser with automatic detection")
            return driver
        except Exception as e:
            print(f"Automatic detection failed: {e}")
            raise Exception("Could not start any webdriver")

    def inject_ws_intercept(self):
        """Inject JavaScript to intercept WebSocket messages."""
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
        """Inject JavaScript to automatically close alerts and popups."""
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
        """Process WebSocket messages and trigger event handlers."""
        try:
            ws_messages = self.driver.execute_script("""
                var messagesCopy = {};
                for (var id in window.myWsMessages) {
                    messagesCopy[id] = window.myWsMessages[id].slice();
                    window.myWsMessages[id] = [];
                }
                return messagesCopy;
            """)
        except Exception as _:
            return
        
        for msg_key, msgs in ws_messages.items():
            for msg in msgs:
                ws_logger.info(f"RECV: ({msg_key}) {msg}")
                if isinstance(msg, list) and len(msg) >= 2:
                    event_type, event_details = msg[0], msg[1]
                    event_key = f"ws_{event_type}"
                    if event_key in self.event_handlers:
                        try:
                            self.event_handlers[event_key](event_details)
                        except Exception as e:
                            ws_logger.info(f"HANDLER_ERROR: {event_key} {e}")
                    elif event_key == "ws_you":
                        self.my_id = event_details

    def send_ws_message(self, contents: list):
        """Send WebSocket message to TagPro."""
        ws_logger.info(f"SEND: {contents}")
        try:
            ws_ids = self.driver.execute_script("return Object.keys(window.myWebSockets || {});")
            if not ws_ids:
                print("no websocket")
                return
        except Exception as e:
            print(f"WebSocket not ready yet: {e}")
            return
        
        ws_id = ws_ids[-1]
        
        # Only send if on a group page
        if not self.driver.current_url.startswith(GROUPS_URL):
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
            print("TODO: LOOK INTO THIS", e)

    def get_lobby_players(self):
        """Get current lobby players organized by team."""
        teams = ["red-team", "blue-team", "spectators", "waiting"]
        lobby_players = {}
        
        for team in teams:
            lobby_players[team] = self.driver.execute_script(f"""
                return Array.from(document.querySelectorAll("#{team} li.player-item")).map(el => {{
                    return {{
                        name: el.querySelector('.player-name') ? el.querySelector('.player-name').innerText : "",
                        location: el.querySelector('.player-location') ? el.querySelector('.player-location').innerText : ""
                    }};
                }});
            """)
        
        return lobby_players

    def find_elements(self, css_selector: str):
        """Find elements by CSS selector."""
        return self.driver.find_elements(By.CSS_SELECTOR, css_selector)

    def is_game_active(self):
        """Return True if the join-game button is displayed."""
        join_game_btns = self.find_elements("#join-game-btn")
        return any(b.is_displayed() for b in join_game_btns)

    def send_chat_msg(self, text: str):
        """Send chat message, splitting on newlines."""
        for line in text.split("\n"):
            self.send_ws_message(["chat", line])

    def get_game_uuid(self):
        """Extract game UUID from client info."""
        for _ in range(5):
            client_info = self.driver.execute_script("return tagpro.clientInfo;")
            if client_info is not None:
                return client_info["gameUuid"]
            time.sleep(1)
        return None

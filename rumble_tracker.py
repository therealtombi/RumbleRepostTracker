# --- COMPATIBILITY PATCH FOR PYTHON 3.12+ ---
import sys
import os

try:
    import distutils.version
except ImportError:
    import setuptools
    import distutils.version
# --------------------------------------------

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import threading
import time
import json
import queue
import hashlib
import logging
import shutil
import requests
import subprocess
import re

# Web & Browser Libraries
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pygame
from flask import Flask, jsonify, send_file

# --- LOGGING SETUP ---
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- CTK CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# --- GLOBAL CONFIGURATION ---
CONFIG_FILE = "tracker_config.json"
HISTORY_FILE = "repost_history.json"
COOKIES_FILE = "saved_cookies.json"
TEMPLATE_FILE = "overlay.html"
ICON_FILE = "icon.ico"

GOOGLE_FONTS = [
    "Roboto", "Open Sans", "Lato", "Montserrat", "Oswald", "Source Sans Pro",
    "Slabo 27px", "Raleway", "PT Sans", "Merriweather", "Noto Sans", "Nunito",
    "Concert One", "Prompt", "Work Sans", "Rubik", "Fjalla One", "Bangers",
    "Poiret One", "Righteous", "Russo One", "Handlee", "Patrick Hand",
    "Creepster", "Anton", "Orbitron", "Luckiest Guy", "Fredoka One",
    "Special Elite", "Teko", "Alfa Slab One", "Audiowide", "Black Ops One",
    "Carter One", "Changa One", "Passion One", "Press Start 2P", "Quantico",
    "Sigmar One", "Squada One", "Syncopate", "Titan One", "Ultra",
    "VT323", "Voltaire", "Wallpoet", "Yeon Sung", "Zilla Slab Highlight"
]

DEFAULT_CONFIG = {
    "sound_file": "",
    "poll_interval": 5,
    "overlay_port": 5050,
    "font_size": 14,
    "repost_limit": 5,
    "font_family": "Roboto",
    "recent_color": "#85c742",
    "older_color": "#ffffff",
    "title_text": "NEW REPOST",
    "title_color": "#ffffff",
    "title_size": 24,
    "title_align": "center",
    "browser_path": "",
    "selected_browser": "Auto-Detect",
    "use_override": False,
    "remember_login": True,
    "audio_volume": 0.5,
    "chrome_version": 0
}

# --- GLOBAL SHARED STATE ---
GLOBAL_CONFIG = DEFAULT_CONFIG.copy()

TRACKER_STATE = {
    "current_alert": None,
    "is_visible": False,
    "audio_timestamp": 0,
    "last_update_id": 0
}

REPOST_QUEUE = queue.Queue()

# --- FLASK WEB SERVER ---
app = Flask(__name__)
app.json.sort_keys = True


@app.after_request
def add_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/')
def index():
    try:
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "Overlay HTML not found. Run app to generate it."


@app.route('/current_sound')
def current_sound():
    path = GLOBAL_CONFIG.get("sound_file", "")
    if path and os.path.exists(path):
        return send_file(path)
    return "No file selected", 404


@app.route('/api/data')
def get_data():
    response = {
        "data": TRACKER_STATE,
        "config": GLOBAL_CONFIG
    }
    return jsonify(response)


def run_flask_server():
    try:
        app.run(host='0.0.0.0', port=5050, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"CRITICAL FLASK ERROR: {e}")


# --- BROWSER DETECTION HELPERS ---
def find_browsers():
    found = {"Auto-Detect": ""}

    prog_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    prog_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "C:\\Users\\Default\\AppData\\Local")

    candidates = {
        "Google Chrome": [
            os.path.join(prog_files, "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(prog_files_x86, "Google\\Chrome\\Application\\chrome.exe")
        ],
        "Brave Browser": [
            os.path.join(prog_files, "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
            os.path.join(prog_files_x86, "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
            os.path.join(local_app_data, "BraveSoftware\\Brave-Browser\\Application\\brave.exe")
        ],
        "Vivaldi": [
            os.path.join(local_app_data, "Vivaldi\\Application\\vivaldi.exe")
        ],
        "Opera": [
            os.path.join(local_app_data, "Programs\\Opera\\launcher.exe"),
            os.path.join(prog_files, "Opera\\launcher.exe")
        ],
        "Opera GX": [
            os.path.join(local_app_data, "Programs\\Opera GX\\launcher.exe")
        ]
    }

    for name, paths in candidates.items():
        for path in paths:
            if os.path.exists(path):
                found[name] = path
                break

    return found


# --- MAIN GUI CLASS ---
class RumbleRepostTracker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Rumble Repost Tracker (Pro)")
        self.geometry("1920x1080")

        if os.path.exists(ICON_FILE):
            try:
                self.iconbitmap(ICON_FILE)
            except:
                pass

        # Audio Init
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Audio Init Error: {e}")

        self.driver = None
        self.is_tracking = False
        self.is_logging_in = False
        self.seen_reposts = self.load_history()
        self.is_muted = tk.BooleanVar(value=False)
        self.test_sound_channel = None
        self.fade_timer = None
        self.test_overlay_timer = None

        self.login_btn_default_color = ["#3B8ED0", "#1F6AA5"]
        self.error_logs = []

        # Configuration Vars
        self.load_config_to_global()

        # Browser Vars
        self.detected_browsers = find_browsers()
        self.browser_map = self.detected_browsers

        if GLOBAL_CONFIG.get("selected_browser") not in self.browser_map:
            GLOBAL_CONFIG["selected_browser"] = "Auto-Detect"

        self.selected_browser_var = tk.StringVar(value=GLOBAL_CONFIG.get("selected_browser", "Auto-Detect"))
        self.custom_browser_path_var = tk.StringVar(value=GLOBAL_CONFIG.get("browser_path", ""))
        self.use_override_var = tk.BooleanVar(value=GLOBAL_CONFIG.get("use_override", False))
        self.remember_login_var = tk.BooleanVar(value=GLOBAL_CONFIG.get("remember_login", True))
        self.chrome_version_var = tk.StringVar(value=str(GLOBAL_CONFIG.get("chrome_version", 0)))

        self.write_template_file()

        self.flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        self.flask_thread.start()

        self.queue_thread = threading.Thread(target=self._queue_processor, daemon=True)
        self.queue_thread.start()

        self.status_var = tk.StringVar(value=f"Ready. Loaded {len(self.seen_reposts)} history items.")
        self.sound_path_var = tk.StringVar(value=GLOBAL_CONFIG.get("sound_file", ""))
        self.font_family_var = tk.StringVar(value=GLOBAL_CONFIG.get("font_family", "Roboto"))
        self.title_text_var = tk.StringVar(value=GLOBAL_CONFIG.get("title_text", "NEW REPOST"))
        self.title_align_var = tk.StringVar(value=GLOBAL_CONFIG.get("title_align", "center"))

        self.current_font_size = GLOBAL_CONFIG.get("font_size", 14)

        self.setup_ui()

        self.title_text_var.trace_add("write", self.update_live_preview)
        self.font_family_var.trace_add("write", self.update_live_preview)
        self.title_align_var.trace_add("write", self.update_live_preview)

        self.bind("<Control-MouseWheel>", self.on_ctrl_scroll)
        self.update_browser_ui_state()

        self.after(1000, self.check_cookie_status)
        self.update_live_preview()

    def log(self, msg):
        self.after(0, lambda: self._log_internal(msg))

    def _log_internal(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {msg}\n"

        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("0.0", full_msg)
        self.log_textbox.configure(state="disabled")
        self.status_label.configure(text=msg)

        lower_msg = msg.lower()
        if any(x in lower_msg for x in ["error", "warning", "exception", "failed", "blocked", "mismatch"]):
            self.error_logs.append(full_msg)
            if hasattr(self, 'txt_error_logs'):
                self.txt_error_logs.configure(state="normal")
                self.txt_error_logs.insert("0.0", full_msg)
                self.txt_error_logs.configure(state="disabled")

    def copy_error_logs(self):
        logs = "".join(self.error_logs)
        if not logs: logs = "No errors recorded."
        self.clipboard_clear()
        self.clipboard_append(logs)
        messagebox.showinfo("Copied", "Error logs copied to clipboard.")

    def email_error_logs(self):
        recipient = "the.real.tombliboos@gmail.com"
        subject = "Rumble Tracker Error Log"
        body_content = "".join(self.error_logs[-20:]) if self.error_logs else "No errors recorded."
        body = f"Please describe the issue here:\n\n\n--- App Error Log (Last 20 entries) ---\n{body_content}"
        params = {"subject": subject, "body": body}
        query = urllib.parse.urlencode(params)
        try:
            webbrowser.open(f"mailto:{recipient}?{query}")
        except Exception as e:
            self.log(f"Failed to open email client: {e}")
            messagebox.showerror("Error", "Could not open email client. Please copy logs manually.")

    # --- PERSISTENCE ---
    def load_config_to_global(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    GLOBAL_CONFIG.update(data)
            except:
                pass

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    return set(json.load(f))
            except:
                pass
        return set()

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(list(self.seen_reposts), f)
        except:
            pass

    def save_config(self):
        GLOBAL_CONFIG["sound_file"] = self.sound_path_var.get()
        GLOBAL_CONFIG["font_family"] = self.font_family_var.get()
        GLOBAL_CONFIG["title_text"] = self.title_text_var.get()
        GLOBAL_CONFIG["title_align"] = self.title_align_var.get()
        GLOBAL_CONFIG["font_size"] = self.current_font_size

        GLOBAL_CONFIG["selected_browser"] = self.selected_browser_var.get()
        GLOBAL_CONFIG["browser_path"] = self.custom_browser_path_var.get()
        GLOBAL_CONFIG["use_override"] = self.use_override_var.get()
        GLOBAL_CONFIG["remember_login"] = self.remember_login_var.get()

        try:
            val = int(self.chrome_version_var.get())
            GLOBAL_CONFIG["chrome_version"] = val
        except:
            GLOBAL_CONFIG["chrome_version"] = 0

        with open(CONFIG_FILE, "w") as f:
            json.dump(GLOBAL_CONFIG, f)

        TRACKER_STATE["last_update_id"] += 1
        self.status_var.set("Settings Saved & Applied!")

    def save_cookies(self):
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
                ua = self.driver.execute_script("return navigator.userAgent")
                with open(COOKIES_FILE, "w") as f:
                    json.dump({"cookies": cookies, "user_agent": ua}, f)
                self.log("Session saved (Cookies + UA).")
            except Exception as e:
                print(f"Failed to save cookies: {e}")

    def load_saved_session(self):
        if os.path.exists(COOKIES_FILE):
            try:
                with open(COOKIES_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return None

    def validate_cookie_expiry(self, session_data):
        if not session_data or "cookies" not in session_data: return False
        cookies = session_data["cookies"]
        current_time = time.time()
        for cookie in cookies:
            if 'expiry' in cookie:
                if cookie['expiry'] < current_time:
                    return False
        return True

    def check_cookie_status(self):
        if not self.remember_login_var.get(): return
        session = self.load_saved_session()
        if not session:
            self.log("No saved login found. Please log in.")
            return
        if self.validate_cookie_expiry(session):
            self.log("Valid saved session found. Ready to track.")
            self.btn_track.configure(state="normal", fg_color="#2CC985")
            self.btn_browser.configure(text="LOGGED IN (Click to Reset)", fg_color="#2CC985", hover_color="#22AA66")
        else:
            self.log("Saved login expired.")
            self.btn_browser.configure(text="1. Login & Capture", fg_color=self.login_btn_default_color[0],
                                       hover_color=self.login_btn_default_color[1])
            try:
                os.remove(COOKIES_FILE)
            except:
                pass

    # --- UI HELPERS ---
    def choose_color(self, config_key, btn_widget):
        curr = GLOBAL_CONFIG.get(config_key, "#ffffff")
        color = colorchooser.askcolor(color=curr, title=f"Choose Color")[1]
        if color:
            GLOBAL_CONFIG[config_key] = color
            btn_widget.configure(fg_color=color, text=color)
            self.save_config()
            self.update_live_preview()

    def set_int_config(self, key, val):
        try:
            GLOBAL_CONFIG[key] = int(val)
            self.save_config()
            self.update_live_preview()
        except:
            pass

    def set_volume_config(self, value):
        GLOBAL_CONFIG["audio_volume"] = float(value)
        self.save_config()
        if self.test_sound_channel:
            self.test_sound_channel.set_volume(float(value))

    def browse_sound(self):
        f = filedialog.askopenfilename(filetypes=[("Audio", "*.wav *.mp3")])
        if f: self.sound_path_var.set(f)

    def toggle_mute(self):
        new_state = not self.is_muted.get()
        self.is_muted.set(new_state)
        if new_state:
            self.btn_mute.configure(text="AUDIO MUTED (Click to Enable)", fg_color="#FF5555", hover_color="#AA0000")
        else:
            self.btn_mute.configure(text="MUTE AUDIO ALERTS", fg_color="#555555", hover_color="#777777")

    def _queue_processor(self):
        while True:
            try:
                alert_data = REPOST_QUEUE.get()
                TRACKER_STATE["current_alert"] = alert_data
                TRACKER_STATE["is_visible"] = True
                audio_path = GLOBAL_CONFIG.get("sound_file", "")
                audio_duration = 0.0
                if audio_path and os.path.exists(audio_path) and not self.is_muted.get():
                    TRACKER_STATE["audio_timestamp"] = time.time()
                    try:
                        sound = pygame.mixer.Sound(audio_path)
                        audio_duration = sound.get_length()
                    except:
                        pass
                display_time = max(10.0, audio_duration)
                time.sleep(display_time)
                TRACKER_STATE["is_visible"] = False
                time.sleep(5.0)
            except Exception as e:
                print(f"Queue Error: {e}")
                time.sleep(1)

    def play_sound(self):
        self.stop_test_sound()
        TRACKER_STATE["audio_timestamp"] = time.time()
        TRACKER_STATE["current_alert"] = {"user": "TEST USER", "video": "Test Video Title"}
        TRACKER_STATE["is_visible"] = True
        f = self.sound_path_var.get()
        duration = 10.0
        if f and os.path.exists(f):
            try:
                sound = pygame.mixer.Sound(f)
                vol = GLOBAL_CONFIG.get("audio_volume", 0.5)
                sound.set_volume(vol)
                self.test_sound_channel = sound.play()
                file_len = sound.get_length()
                if file_len > 20:
                    self.fade_timer = self.after(18000, lambda: self.test_sound_channel.fadeout(2000))
                    duration = 20.0
                else:
                    duration = max(10.0, file_len)
            except:
                pass
        self.test_overlay_timer = self.after(int(duration * 1000), self.stop_test_overlay)

    def stop_test_overlay(self):
        TRACKER_STATE["is_visible"] = False
        if self.test_overlay_timer:
            self.after_cancel(self.test_overlay_timer)
            self.test_overlay_timer = None

    def stop_test_sound(self):
        if self.fade_timer:
            self.after_cancel(self.fade_timer)
            self.fade_timer = None
        if self.test_sound_channel:
            self.test_sound_channel.stop()
            self.test_sound_channel = None
        else:
            pygame.mixer.stop()
        self.stop_test_overlay()

    def browse_browser_exe(self):
        f = filedialog.askopenfilename(filetypes=[("Executables", "*.exe")])
        if f: self.custom_browser_path_var.set(f)

    def update_browser_ui_state(self, *args):
        if self.use_override_var.get():
            self.cb_browser_select.configure(state="disabled")
            self.btn_browse_exe.configure(state="normal")
            self.entry_browser_path.configure(state="normal")
        else:
            self.cb_browser_select.configure(state="normal")
            self.btn_browse_exe.configure(state="disabled")
            self.entry_browser_path.configure(state="disabled")

    # --- ROBUST BROWSER LAUNCHER ---
    def _safe_driver_launch(self):
        """Attempts to launch driver, handling version mismatch automatically."""
        # 1. Get Initial Options
        opts = self.get_browser_options()

        # 2. Check for manual override from Config
        ver_arg = self.get_chrome_version_arg()
        if ver_arg:
            self.log(f"Using forced driver version: {ver_arg}")
            return uc.Chrome(options=opts, version_main=ver_arg)

        # 3. Try Default Auto-Detect Launch
        try:
            return uc.Chrome(options=opts)
        except Exception as e:
            err_msg = str(e)

            # 4. Catch Version Mismatch
            # Example error: "... Current browser version is 144.0.7559.110 ..."
            if "Current browser version is" in err_msg:
                self.log("Browser version mismatch detected. Attempting auto-fix...")

                # Regex to extract the major version number
                match = re.search(r"Current browser version is (\d+)\.", err_msg)
                if match:
                    detected_version = int(match.group(1))
                    self.log(f"Auto-detected version {detected_version}. Retrying...")

                    # IMPORTANT: Must generate FRESH options for the retry!
                    # Reusing the old 'opts' object causes "cannot reuse ChromeOptions" error.
                    new_opts = self.get_browser_options()
                    return uc.Chrome(options=new_opts, version_main=detected_version)

            # If not a version error or fix failed, re-raise
            raise e

    def get_browser_options(self, binary_path=""):
        opts = uc.ChromeOptions()
        opts.add_argument("--mute-audio")
        opts.add_argument("--disable-gpu")

        if not binary_path:
            if self.use_override_var.get():
                binary_path = self.custom_browser_path_var.get()
            else:
                selection = self.selected_browser_var.get()
                if selection in self.browser_map and self.browser_map[selection]:
                    binary_path = self.browser_map[selection]

        if binary_path:
            opts.binary_location = binary_path

        return opts

    def get_chrome_version_arg(self):
        try:
            v = int(GLOBAL_CONFIG.get("chrome_version", 0))
            return v if v > 0 else None
        except:
            return None

    def start_login_process(self):
        if self.btn_browser.cget("text").startswith("LOGGED IN"):
            if messagebox.askyesno("Reset Login", "Do you want to clear your saved session and log in again?"):
                try:
                    os.remove(COOKIES_FILE)
                except:
                    pass
                self.btn_browser.configure(text="1. Login & Capture", fg_color=self.login_btn_default_color[0],
                                           hover_color=self.login_btn_default_color[1])
                self.btn_track.configure(state="disabled", fg_color="gray")
                self.log("Session cleared.")
            return

        if self.is_logging_in or self.is_tracking: return
        self.is_logging_in = True
        self.btn_browser.configure(state="disabled", text="Waiting for Login...")
        threading.Thread(target=self._run_login_monitor, daemon=True).start()

    def _run_login_monitor(self):
        self.log("Opening Browser for Login...")

        try:
            # Use Safe Launcher
            self.driver = self._safe_driver_launch()
            self.driver.get("https://rumble.com/login.php")
            self.log("Please log in manually.")

            while self.is_logging_in:
                if not self.driver: break
                try:
                    bell = self.driver.find_elements(By.CSS_SELECTOR, ".user-notifications--bell-button")
                    if bell:
                        self.log("Login Detected! Saving session...")
                        self.save_cookies()
                        time.sleep(1)
                        self.driver.quit()
                        self.driver = None
                        self.log("Login successful. Window closed.")
                        self.after(0, lambda: self.btn_track.configure(state="normal", fg_color="#2CC985"))
                        self.after(0,
                                   lambda: self.btn_browser.configure(state="normal", text="LOGGED IN (Click to Reset)",
                                                                      fg_color="#2CC985", hover_color="#22AA66"))
                        break
                except:
                    pass
                time.sleep(1)

        except Exception as e:
            self.log(f"Login Init Error: {e}")
            if "session not created" in str(e).lower():
                self.after(0, lambda: messagebox.showerror("Version Error", f"Driver Error:\n{str(e)[:200]}..."))
            self.driver = None
            self.after(0, lambda: self.btn_browser.configure(state="normal", text="1. Login & Capture"))

        self.is_logging_in = False

    def toggle_tracking(self):
        if not self.is_tracking:
            self.is_tracking = True
            self.btn_track.configure(text="Stop Tracking", fg_color="#FF5555", hover_color="#AA0000")
            threading.Thread(target=self._tracker_loop_fetch, daemon=True).start()
        else:
            self.is_tracking = False
            self.btn_track.configure(text="Start Tracking", fg_color="#2CC985", hover_color="#22AA66")
            self.log("Tracking Stopped.")

    def _tracker_loop_fetch(self):
        self.log("Starting API Tracker (Fetch Mode)...")
        session_data = self.load_saved_session()
        if not session_data or "cookies" not in session_data:
            self.log("No valid session found. Please Login.")
            self.after(0, self.toggle_tracking)
            return

        s = requests.Session()
        for c in session_data["cookies"]:
            s.cookies.set(c['name'], c['value'], domain=c['domain'])

        headers = {
            "User-Agent": session_data.get("user_agent",
                                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://rumble.com/",
        }
        api_url = "https://rumble.com/service.php?name=user.notification_feed&limit=25"
        self.log(f"Tracking Active. Interval: {GLOBAL_CONFIG['poll_interval']}s")

        while self.is_tracking:
            try:
                r = s.get(api_url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    if "data" in data and "items" in data["data"]:
                        items = data["data"]["items"]
                        batch_reposts = []
                        for item in items:
                            is_repost = False
                            user_name = "Unknown"
                            video_title = "Video"
                            if item.get("type") == "video_reposted":
                                is_repost = True
                                user_obj = item.get("user", {})
                                video_obj = item.get("video", {})
                                user_name = user_obj.get("username", user_obj.get("name", "Unknown"))
                                video_title = video_obj.get("title", "Unknown Video")
                            elif "reposted" in item.get("body", "").lower():
                                is_repost = True
                                if "user" in item:
                                    user_name = item["user"].get("username", "Unknown")
                            if is_repost:
                                unique_str = f"{user_name}_{video_title}_{item.get('created_on', '')}"
                                n_id = hashlib.md5(unique_str.encode('utf-8')).hexdigest()
                                if n_id not in self.seen_reposts:
                                    self.seen_reposts.add(n_id)
                                    self.save_history()
                                    batch_reposts.append({"user": user_name, "video": video_title})
                                    self.log(f"NEW REPOST: {user_name}")
                        for item in reversed(batch_reposts):
                            REPOST_QUEUE.put(item)
                elif r.status_code == 403:
                    self.log("Session Blocked (403). Switching to Browser Mode...")
                    self.is_tracking = False
                    self.driver = None
                    threading.Thread(target=self._tracker_loop, daemon=True).start()
                    break
                else:
                    self.log(f"API Error: {r.status_code}")
            except Exception as e:
                self.log(f"Fetch Error: {e}")
            time.sleep(int(GLOBAL_CONFIG['poll_interval']))

    def _tracker_loop(self):
        self.log("Starting Browser Tracker (Hidden)...")
        self.is_tracking = True
        session_data = self.load_saved_session()

        try:
            # Use Safe Launcher
            self.driver = self._safe_driver_launch()
            self.driver.minimize_window()

            if session_data:
                self.driver.get("https://rumble.com/404")
                for c in session_data["cookies"]:
                    try:
                        self.driver.add_cookie(c)
                    except:
                        pass
                self.driver.get("https://rumble.com")
        except Exception as e:
            self.log(f"Fallback Error: {e}")
            self.is_tracking = False
            return

        while self.is_tracking:
            if not self.driver: break
            try:
                self.driver.refresh()
                time.sleep(3)
                bell = self.driver.find_element(By.CSS_SELECTOR, ".user-notifications--bell-button")
                self.driver.execute_script("arguments[0].click();", bell)
                time.sleep(1.5)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                notif_list = soup.find("ul", class_="user-notifications--list")
                if notif_list:
                    items = notif_list.find_all("li")
                    batch_reposts = []
                    for li in items:
                        text_div = li.find("div", class_="user-notifications--text")
                        if not text_div: continue
                        body_div = text_div.find("div", class_="user-notifications--body")
                        if not body_div: continue
                        full_text = body_div.get_text(" ", strip=True)
                        if "reposted your video" in full_text:
                            n_id = hashlib.md5(full_text.encode('utf-8')).hexdigest()
                            if n_id not in self.seen_reposts:
                                self.seen_reposts.add(n_id)
                                self.save_history()
                                user_link = body_div.find("a")
                                user = user_link.text if user_link else "Unknown"
                                vid_title = "Unknown"
                                if '"' in full_text:
                                    parts = full_text.split('"')
                                    if len(parts) > 1: vid_title = parts[1]
                                batch_reposts.append({"user": user, "video": vid_title})
                                self.log(f"NEW REPOST: {user}")
                    for item in reversed(batch_reposts):
                        REPOST_QUEUE.put(item)
            except Exception as e:
                if "invalid session id" in str(e).lower(): break
            time.sleep(int(GLOBAL_CONFIG['poll_interval']))

        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def on_close(self):
        self.is_tracking = False
        try:
            if self.driver: self.driver.quit()
        except:
            pass
        self.destroy()
        sys.exit(0)

    # --- SCALING ---
    def on_ctrl_scroll(self, event, manual_delta=None):
        delta = manual_delta if manual_delta else event.delta
        if delta > 0:
            self.current_font_size += 1
        else:
            self.current_font_size -= 1
        self.current_font_size = max(8, min(self.current_font_size, 30))
        self.lbl_title.configure(font=ctk.CTkFont(family="Arial", size=self.current_font_size + 6, weight="bold"))
        GLOBAL_CONFIG['title_size'] = self.current_font_size
        self.update_live_preview()

    def update_app_fonts(self):
        pass

        # --- LIVE PREVIEW UPDATE LOGIC ---

    def update_live_preview(self, *args):
        self.lbl_prev_header.configure(text=self.title_text_var.get())
        fam = self.font_family_var.get()
        if not fam: fam = "Roboto"
        title_size = int(GLOBAL_CONFIG.get('title_size', 24))
        self.lbl_prev_header.configure(font=(fam, title_size, "bold"))
        self.lbl_prev_user.configure(font=(fam, 32, "bold"))
        self.lbl_prev_video.configure(font=(fam, 18, "italic"))
        self.lbl_prev_header.configure(text_color=GLOBAL_CONFIG.get('title_color', '#ffffff'))
        self.lbl_prev_user.configure(text_color=GLOBAL_CONFIG.get('recent_color', '#85c742'))
        self.lbl_prev_video.configure(text_color=GLOBAL_CONFIG.get('older_color', '#ffffff'))
        align_map = {"left": "w", "center": "center", "right": "e"}
        alignment = align_map.get(self.title_align_var.get(), "center")
        self.lbl_prev_header.configure(anchor=alignment)
        self.lbl_prev_user.configure(anchor=alignment)
        self.lbl_prev_video.configure(anchor=alignment)

    # --- NEW: LAUNCH WEB PREVIEW POPUP ---
    def launch_web_preview(self):
        url = "http://127.0.0.1:5050"
        binary = None
        if self.use_override_var.get():
            binary = self.custom_browser_path_var.get()
        else:
            selection = self.selected_browser_var.get()
            if selection in self.browser_map:
                binary = self.browser_map[selection]
        if binary and os.path.exists(binary):
            try:
                subprocess.Popen([binary, f"--app={url}", "--window-size=600,250"])
            except Exception as e:
                self.log(f"Error launching preview: {e}")
                import webbrowser
                webbrowser.open(url)
        else:
            import webbrowser
            webbrowser.open(url)

    def write_template_file(self):
        # (Template omitted for brevity)
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Rumble Overlay</title>
    <style>
        body { margin: 0; padding: 20px; overflow: hidden; background: transparent; font-family: sans-serif; }

        #container {
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 600px;
            background: rgba(20, 20, 20, 0.9);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            border: 2px solid #85c742;

            opacity: 0;
            transform: translateY(20px) scale(0.95);
            transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        #container.visible {
            opacity: 1;
            transform: translateY(0) scale(1);
        }

        .header {
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }

        .user-name {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }

        .video-title {
            font-size: 18px;
            font-style: italic;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="header" class="header"></div>
        <div id="content">
            <div id="user" class="user-name"></div>
            <div id="video" class="video-title"></div>
        </div>
    </div>

    <script>
        const API_URL = "http://127.0.0.1:5050";

        let currentConfigStr = "";
        const audio = new Audio();
        let lastPlayedAudioTime = 0;
        let fadeTimer = null;

        function loadGoogleFont(fontName) {
            if (!fontName) return;
            const linkId = 'google-font-link';
            let link = document.getElementById(linkId);
            if (!link) {
                link = document.createElement('link');
                link.id = linkId;
                link.rel = 'stylesheet';
                document.head.appendChild(link);
            }
            link.href = `https://fonts.googleapis.com/css?family=${fontName.replace(/ /g, '+')}`;
            document.body.style.fontFamily = `'${fontName}', sans-serif`;
        }

        function fadeOutAudio(duration) {
            const step = 0.05;
            const interval = duration / (1.0 / step);

            const fade = setInterval(() => {
                if (audio.volume > step) {
                    audio.volume -= step;
                } else {
                    audio.volume = 0;
                    audio.pause();
                    audio.currentTime = 0;
                    clearInterval(fade);
                }
            }, interval);
        }

        function update() {
            fetch(API_URL + '/api/data?t=' + new Date().getTime())
                .then(r => r.json())
                .then(resp => {
                    const data = resp.data;
                    const config = resp.config;

                    const container = document.getElementById('container');
                    const headerDiv = document.getElementById('header');
                    const userDiv = document.getElementById('user');
                    const videoDiv = document.getElementById('video');

                    const configStr = JSON.stringify(config);
                    if (configStr !== currentConfigStr) {
                        loadGoogleFont(config.font_family);
                        container.style.textAlign = config.title_align;
                        headerDiv.innerText = config.title_text;
                        headerDiv.style.color = config.title_color;
                        headerDiv.style.fontSize = config.title_size + "px";
                        userDiv.style.color = config.recent_color;
                        videoDiv.style.color = config.older_color;

                        audio.src = API_URL + "/current_sound?t=" + new Date().getTime();
                        audio.load();

                        currentConfigStr = configStr;
                    }

                    if (data.audio_timestamp > lastPlayedAudioTime) {
                        lastPlayedAudioTime = data.audio_timestamp;

                        if(fadeTimer) clearTimeout(fadeTimer);

                        audio.currentTime = 0;
                        audio.volume = config.audio_volume !== undefined ? config.audio_volume : 1.0; 

                        var playPromise = audio.play();
                        if (playPromise !== undefined) {
                            playPromise.then(() => {
                                fadeTimer = setTimeout(() => {
                                    fadeOutAudio(2000); 
                                }, 18000);
                            }).catch(error => {
                                console.log("Audio play failed: " + error);
                            });
                        }
                    }

                    if (data.is_visible && data.current_alert) {
                        if (!container.classList.contains('visible') || userDiv.innerText !== data.current_alert.user) {
                            userDiv.innerText = data.current_alert.user;
                            videoDiv.innerText = data.current_alert.video;
                        }
                        container.classList.add('visible');
                    } else {
                        container.classList.remove('visible');
                    }
                })
                .catch(e => { });
        }

        setInterval(update, 500);
    </script>
</body>
</html>
        """
        try:
            with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception as e:
            print(f"Error writing template: {e}")

    # --- UI SETUP ---
    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Controls")
        self.tabview.add("Style & Config")
        self.tabview.add("Error Logs")

        # === TAB 1: CONTROLS ===
        tab_main = self.tabview.tab("Controls")

        self.lbl_title = ctk.CTkLabel(tab_main, text="Rumble Repost Tracker", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=10)

        # Browser Frame
        browser_frame = ctk.CTkFrame(tab_main)
        browser_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(browser_frame, text="Browser Configuration", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=10, pady=(10, 5))

        f_row1 = ctk.CTkFrame(browser_frame, fg_color="transparent")
        f_row1.pack(fill="x", pady=2, padx=10)
        ctk.CTkLabel(f_row1, text="Browser In Use:").pack(side="left")

        browser_names = list(self.browser_map.keys())
        self.cb_browser_select = ctk.CTkComboBox(f_row1, variable=self.selected_browser_var, values=browser_names)
        self.cb_browser_select.pack(side="left", fill="x", expand=True, padx=10)

        f_row2 = ctk.CTkFrame(browser_frame, fg_color="transparent")
        f_row2.pack(fill="x", pady=5, padx=10)

        chk_override = ctk.CTkCheckBox(f_row2, text="Manual Override Path", variable=self.use_override_var,
                                       command=self.update_browser_ui_state)
        chk_override.pack(side="left")

        self.entry_browser_path = ctk.CTkEntry(f_row2, textvariable=self.custom_browser_path_var)
        self.entry_browser_path.pack(side="left", fill="x", expand=True, padx=10)

        self.btn_browse_exe = ctk.CTkButton(f_row2, text="Browse...", command=self.browse_browser_exe, width=80)
        self.btn_browse_exe.pack(side="left")

        # --- NEW: FORCE VERSION ROW ---
        f_row3 = ctk.CTkFrame(browser_frame, fg_color="transparent")
        f_row3.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(f_row3, text="Force Driver Version (0=Auto):").pack(side="left")

        self.entry_chrome_version = ctk.CTkEntry(f_row3, textvariable=self.chrome_version_var, width=50)
        self.entry_chrome_version.pack(side="left", padx=5)
        # ------------------------------

        # --- LOGIN ROW CONTAINER ---
        login_row_frame = ctk.CTkFrame(tab_main, fg_color="transparent")
        login_row_frame.pack(fill="x", padx=40, pady=10)

        self.chk_remember_login = ctk.CTkCheckBox(login_row_frame, text="Remember Login",
                                                  variable=self.remember_login_var, command=self.save_config)
        self.chk_remember_login.pack(side="left", padx=(0, 10))

        self.btn_browser = ctk.CTkButton(login_row_frame, text="1. Login & Capture", command=self.start_login_process,
                                         height=40)
        self.btn_browser.pack(side="left", fill="x", expand=True)

        self.btn_track = ctk.CTkButton(tab_main, text="2. Start Tracking (Background)", command=self.toggle_tracking,
                                       height=40, state="disabled", fg_color="gray")
        self.btn_track.pack(fill="x", padx=40, pady=10)

        frame_obs = ctk.CTkFrame(tab_main)
        frame_obs.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(frame_obs, text="OBS Setup (Recommended)", font=ctk.CTkFont(weight="bold")).pack(anchor="w",
                                                                                                      padx=10,
                                                                                                      pady=(5, 0))
        ctk.CTkLabel(frame_obs, text="1. In OBS, Add Source -> Browser").pack(anchor="w", padx=10, pady=(0, 5))
        ctk.CTkLabel(frame_obs, text="2. Check 'Local file'").pack(anchor="w", padx=10, pady=(0, 5))
        ctk.CTkLabel(frame_obs, text="3. Select 'overlay.html' from the app folder").pack(anchor="w", padx=10,
                                                                                          pady=(0, 5))

        frame_link = ctk.CTkFrame(tab_main)
        frame_link.pack(fill="x", padx=20, pady=5)
        btn_copy = ctk.CTkButton(frame_link, text="Copy URL (http://127.0.0.1:5050)",
                                 command=lambda: [self.clipboard_clear(),
                                                  self.clipboard_append("http://127.0.0.1:5050"),
                                                  self.status_var.set("URL Copied!")],
                                 fg_color="#3B8ED0", hover_color="#1F6AA5")
        btn_copy.pack(fill="x", padx=5, pady=5)

        self.log_textbox = ctk.CTkTextbox(tab_main, height=150)
        self.log_textbox.pack(fill="both", padx=20, pady=10, expand=True)
        self.log_textbox.configure(state="disabled")

        self.btn_mute = ctk.CTkButton(tab_main, text="MUTE AUDIO ALERTS", command=self.toggle_mute, height=40,
                                      fg_color="#555555", hover_color="#777777")
        self.btn_mute.pack(fill="x", padx=40, pady=10)

        self.status_label = ctk.CTkLabel(tab_main, textvariable=self.status_var, anchor="w", fg_color="transparent")
        self.status_label.pack(side="bottom", fill="x", padx=20, pady=5)

        # === TAB 2: STYLE ===
        tab_style = self.tabview.tab("Style & Config")

        self.frame_preview = ctk.CTkFrame(tab_style, fg_color="#141414", border_color="#85c742", border_width=2,
                                          corner_radius=12)
        self.frame_preview.pack(fill="x", padx=20, pady=(20, 10))

        self.lbl_prev_header = ctk.CTkLabel(self.frame_preview, text="NEW REPOST", font=("Roboto", 24, "bold"))
        self.lbl_prev_header.pack(fill="x", padx=10, pady=(15, 5))

        self.lbl_prev_user = ctk.CTkLabel(self.frame_preview, text="RumbleUser123", font=("Roboto", 32, "bold"))
        self.lbl_prev_user.pack(fill="x", padx=10, pady=2)

        self.lbl_prev_video = ctk.CTkLabel(self.frame_preview, text="Just Reposted This Video!",
                                           font=("Roboto", 18, "italic"))
        self.lbl_prev_video.pack(fill="x", padx=10, pady=(0, 15))

        btn_launch_prev = ctk.CTkButton(tab_style, text="🚀 Pop-out Web Preview (Show Real Fonts)",
                                        command=self.launch_web_preview, height=30, fg_color="#555555",
                                        hover_color="#777777")
        btn_launch_prev.pack(fill="x", padx=20, pady=5)

        frame_font = ctk.CTkFrame(tab_style)
        frame_font.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_font, text="Google Font:").pack(side="left", padx=10)

        self.cb_font_family = ctk.CTkComboBox(frame_font, variable=self.font_family_var, values=GOOGLE_FONTS, width=200,
                                              command=lambda x: self.update_live_preview())
        self.cb_font_family.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        frame_title = ctk.CTkFrame(tab_style)
        frame_title.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_title, text="Title Text:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkEntry(frame_title, textvariable=self.title_text_var).grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(frame_title, text="Size:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkSlider(frame_title, from_=10, to=50, command=lambda v: self.set_int_config('title_size', v)).grid(row=1,
                                                                                                                 column=1,
                                                                                                                 sticky="ew",
                                                                                                                 padx=10,
                                                                                                                 pady=5)

        ctk.CTkLabel(frame_title, text="Align:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ctk.CTkComboBox(frame_title, variable=self.title_align_var, values=["left", "center", "right"],
                        command=lambda x: self.update_live_preview()).grid(row=2, column=1, sticky="ew", padx=10,
                                                                           pady=5)
        frame_title.grid_columnconfigure(1, weight=1)

        frame_col = ctk.CTkFrame(tab_style)
        frame_col.pack(fill="x", padx=10, pady=10)

        btn_t_col = ctk.CTkButton(frame_col, text="Header Color", fg_color=GLOBAL_CONFIG['title_color'],
                                  text_color="black",
                                  command=lambda: self.choose_color('title_color', btn_t_col))
        btn_t_col.pack(fill="x", pady=5, padx=10)

        btn_r_col = ctk.CTkButton(frame_col, text="Username Color", fg_color=GLOBAL_CONFIG['recent_color'],
                                  text_color="black",
                                  command=lambda: self.choose_color('recent_color', btn_r_col))
        btn_r_col.pack(fill="x", pady=5, padx=10)

        btn_o_col = ctk.CTkButton(frame_col, text="Video Title Color", fg_color=GLOBAL_CONFIG['older_color'],
                                  text_color="black",
                                  command=lambda: self.choose_color('older_color', btn_o_col))
        btn_o_col.pack(fill="x", pady=5, padx=10)

        frame_audio = ctk.CTkFrame(tab_style)
        frame_audio.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_audio, text="Alert Sound").pack(side="top", pady=(5, 0))

        ctk.CTkLabel(frame_audio, text="Volume:").pack(side="left", padx=5)
        slider_vol = ctk.CTkSlider(frame_audio, from_=0.0, to=1.0, command=self.set_volume_config)
        slider_vol.set(GLOBAL_CONFIG.get("audio_volume", 0.5))
        slider_vol.pack(side="left", fill="x", expand=True, padx=5)

        f_audio_btns = ctk.CTkFrame(frame_audio, fg_color="transparent")
        f_audio_btns.pack(side="bottom", pady=10)
        ctk.CTkButton(f_audio_btns, text="Browse", command=self.browse_sound, width=80).pack(side="left", padx=5)
        ctk.CTkButton(f_audio_btns, text="Test", command=self.play_sound, width=80).pack(side="left", padx=5)
        ctk.CTkButton(f_audio_btns, text="Stop", command=self.stop_test_sound, fg_color="#FF5555",
                      hover_color="#AA0000", width=80).pack(side="left", padx=5)

        ctk.CTkButton(tab_style, text="Apply & Save All", command=self.save_config, height=40, fg_color="#2CC985",
                      hover_color="#22AA66").pack(fill="x", padx=20, pady=20)

        # === TAB 3: ERROR LOGS ===
        tab_logs = self.tabview.tab("Error Logs")

        ctk.CTkLabel(tab_logs, text="Error & Warning Log", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        self.txt_error_logs = ctk.CTkTextbox(tab_logs, height=300)
        self.txt_error_logs.pack(fill="both", expand=True, padx=10, pady=5)
        self.txt_error_logs.configure(state="disabled")

        btn_frame = ctk.CTkFrame(tab_logs, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Copy to Clipboard", command=self.copy_error_logs).pack(side="left", expand=True,
                                                                                              padx=5)
        ctk.CTkButton(btn_frame, text="Email Support", command=self.email_error_logs, fg_color="#3B8ED0",
                      hover_color="#1F6AA5").pack(side="left", expand=True, padx=5)


if __name__ == "__main__":
    app = RumbleRepostTracker()
    app.mainloop()
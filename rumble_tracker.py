# --- PATCH FOR PYTHON 3.12+ ---
import sys
import os

try:
    import distutils.version
except ImportError:
    import setuptools
    import distutils.version
# ------------------------------

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import threading
import time
import json
import queue
import hashlib  # Required for stable IDs across restarts
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pygame
from flask import Flask, render_template, jsonify
import logging

# Disable Flask Logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- CONFIGURATION & GLOBALS ---
CONFIG_FILE = "tracker_config.json"
HISTORY_FILE = "repost_history.json"  # New file for persistence
TEMPLATE_DIR = "templates"
TEMPLATE_FILE = os.path.join(TEMPLATE_DIR, "overlay.html")

DEFAULT_CONFIG = {
    "sound_file": "",
    "poll_interval": 5,
    "overlay_port": 5000,
    "font_size": 10,
    # Style Configs
    "font_family": "Roboto",
    "recent_color": "#85c742",
    "older_color": "#ffffff",
    "title_text": "NEW REPOST",
    "title_color": "#ffffff",
    "title_size": 24,
    "title_align": "center"
}

# Thread-safe global state
GLOBAL_CONFIG = DEFAULT_CONFIG.copy()

TRACKER_STATE = {
    "current_alert": None,
    "is_visible": False,
    "last_update_id": 0
}

# Queue for holding incoming reposts
REPOST_QUEUE = queue.Queue()

# --- FLASK SERVER ---
app = Flask(__name__)
app.json.sort_keys = True


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r


@app.route('/')
def index():
    return render_template('overlay.html')


@app.route('/api/data')
def get_data():
    response = {
        "data": TRACKER_STATE,
        "config": GLOBAL_CONFIG
    }
    return jsonify(response)


def run_flask():
    try:
        app.run(host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"Flask Error: {e}")


# --- MAIN APPLICATION ---
class RumbleRepostTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Rumble Repost Tracker (Persistent)")
        self.root.geometry("650x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Audio Init
        try:
            pygame.mixer.init()
        except:
            pass

        self.driver = None
        self.is_tracking = False
        self.is_muted = tk.BooleanVar(value=False)

        # 1. Load Config
        self.load_config_to_global()
        # 2. Load History (Persistence)
        self.seen_reposts = self.load_history()
        # 3. Ensure Template
        self.write_template_file()

        # Start Threads
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()

        self.queue_thread = threading.Thread(target=self._queue_processor, daemon=True)
        self.queue_thread.start()

        # UI Variables
        self.status_var = tk.StringVar(value=f"Status: Loaded {len(self.seen_reposts)} previous reposts.")
        self.sound_path_var = tk.StringVar(value=GLOBAL_CONFIG.get("sound_file", ""))
        self.font_family_var = tk.StringVar(value=GLOBAL_CONFIG.get("font_family", "Roboto"))
        self.title_text_var = tk.StringVar(value=GLOBAL_CONFIG.get("title_text", "NEW REPOST"))
        self.title_align_var = tk.StringVar(value=GLOBAL_CONFIG.get("title_align", "center"))

        self.current_font_size = GLOBAL_CONFIG.get("font_size", 10)

        self.setup_ui()
        self.update_app_fonts()

        # Bindings
        self.root.bind("<Control-MouseWheel>", self.on_ctrl_scroll)
        self.root.bind("<Control-Button-4>", lambda e: self.on_ctrl_scroll(e, 1))
        self.root.bind("<Control-Button-5>", lambda e: self.on_ctrl_scroll(e, -1))

    # --- PERSISTENCE METHODS ---
    def load_config_to_global(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    GLOBAL_CONFIG.update(data)
            except:
                pass

    def load_history(self):
        """Loads previously seen repost hashes so we don't alert twice."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)
                    # Return as a set for fast lookup
                    return set(data)
            except Exception as e:
                print(f"Error loading history: {e}")
        return set()

    def save_history(self):
        """Saves current seen reposts to disk."""
        try:
            with open(HISTORY_FILE, "w") as f:
                # Convert set to list for JSON serialization
                json.dump(list(self.seen_reposts), f)
        except Exception as e:
            print(f"Error saving history: {e}")

    def save_config(self):
        GLOBAL_CONFIG["sound_file"] = self.sound_path_var.get()
        GLOBAL_CONFIG["font_family"] = self.font_family_var.get()
        GLOBAL_CONFIG["title_text"] = self.title_text_var.get()
        GLOBAL_CONFIG["title_align"] = self.title_align_var.get()
        GLOBAL_CONFIG["font_size"] = self.current_font_size

        with open(CONFIG_FILE, "w") as f:
            json.dump(GLOBAL_CONFIG, f)

        TRACKER_STATE["last_update_id"] += 1
        self.status_var.set("Configuration Saved!")

    def write_template_file(self):
        if not os.path.exists(TEMPLATE_DIR): os.makedirs(TEMPLATE_DIR)

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
            /* Styling for the Alert Box */
            background: rgba(20, 20, 20, 0.9);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            border: 2px solid #85c742;

            /* Animation State */
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
        let currentConfigStr = "";

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

        function update() {
            fetch('/api/data?t=' + new Date().getTime())
                .then(r => r.json())
                .then(resp => {
                    const data = resp.data;
                    const config = resp.config;

                    const container = document.getElementById('container');
                    const headerDiv = document.getElementById('header');
                    const userDiv = document.getElementById('user');
                    const videoDiv = document.getElementById('video');

                    // 1. APPLY STYLES
                    const configStr = JSON.stringify(config);
                    if (configStr !== currentConfigStr) {
                        loadGoogleFont(config.font_family);

                        container.style.textAlign = config.title_align;

                        headerDiv.innerText = config.title_text;
                        headerDiv.style.color = config.title_color;
                        headerDiv.style.fontSize = config.title_size + "px";

                        userDiv.style.color = config.recent_color;
                        videoDiv.style.color = config.older_color;

                        currentConfigStr = configStr;
                    }

                    // 2. SHOW / HIDE ANIMATION
                    if (data.is_visible && data.current_alert) {
                        // Update text only if changing to prevent jitter
                        if (!container.classList.contains('visible') || userDiv.innerText !== data.current_alert.user) {
                            userDiv.innerText = data.current_alert.user;
                            videoDiv.innerText = data.current_alert.video;
                        }
                        container.classList.add('visible');
                    } else {
                        container.classList.remove('visible');
                    }
                })
                .catch(e => console.log(e));
        }

        setInterval(update, 500); 
    </script>
</body>
</html>
        """
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)

    # --- UI SETUP ---
    def setup_ui(self):
        tabs = ttk.Notebook(self.root)
        self.tab_main = ttk.Frame(tabs)
        self.tab_style = ttk.Frame(tabs)
        tabs.add(self.tab_main, text="Controls")
        tabs.add(self.tab_style, text="Style & Config")
        tabs.pack(expand=1, fill="both")

        # === TAB 1: CONTROLS ===
        self.lbl_title = tk.Label(self.tab_main, text="Rumble Repost Tracker", font=("Arial", 16, "bold"))
        self.lbl_title.pack(pady=10)

        self.btn_browser = tk.Button(self.tab_main, text="1. Open Browser & Login", command=self.start_browser,
                                     bg="#e0e0e0", height=2)
        self.btn_browser.pack(fill="x", padx=40, pady=5)

        self.btn_track = tk.Button(self.tab_main, text="2. Start Tracking", command=self.toggle_tracking, bg="#90ee90",
                                   height=2, state="disabled")
        self.btn_track.pack(fill="x", padx=40, pady=5)

        # Mute Button
        self.btn_mute = tk.Checkbutton(self.tab_main, text="MUTE AUDIO ALERTS", variable=self.is_muted,
                                       font=("Arial", 12, "bold"), fg="red", selectcolor="black", indicatoron=0,
                                       height=2)
        self.btn_mute.pack(fill="x", padx=60, pady=15)

        # OBS Section
        frame_obs = tk.LabelFrame(self.tab_main, text="OBS Integration", padx=10, pady=10)
        frame_obs.pack(fill="x", padx=20, pady=10)

        btn_copy = tk.Button(frame_obs, text="Copy Overlay URL to Clipboard",
                             command=lambda: [self.root.clipboard_clear(),
                                              self.root.clipboard_append("http://127.0.0.1:5000"),
                                              self.status_var.set("URL Copied!")],
                             bg="#add8e6")
        btn_copy.pack(fill="x")

        # Logs
        self.log_list = tk.Listbox(self.tab_main, height=8)
        self.log_list.pack(fill="both", padx=20, pady=10, expand=True)

        self.lbl_status = tk.Label(self.tab_main, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor="w")
        self.lbl_status.pack(side="bottom", fill="x")

        # === TAB 2: STYLE ===
        frame_font = tk.LabelFrame(self.tab_style, text="Fonts & Layout", padx=5, pady=5)
        frame_font.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_font, text="Google Font:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_font, textvariable=self.font_family_var, width=15).grid(row=0, column=1, sticky="ew")

        # Header Settings
        frame_title = tk.LabelFrame(self.tab_style, text="Header Text", padx=5, pady=5)
        frame_title.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_title, text="Title:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_title, textvariable=self.title_text_var).grid(row=0, column=1, sticky="ew")

        tk.Label(frame_title, text="Size:").grid(row=1, column=0, sticky="w")
        sc_title = tk.Scale(frame_title, from_=10, to=50, orient="horizontal",
                            command=lambda v: self.set_int_config('title_size', v))
        sc_title.set(GLOBAL_CONFIG['title_size'])
        sc_title.grid(row=1, column=1, sticky="ew")

        tk.Label(frame_title, text="Align:").grid(row=2, column=0, sticky="w")
        cb_align = ttk.Combobox(frame_title, textvariable=self.title_align_var, values=["left", "center", "right"],
                                state="readonly")
        cb_align.grid(row=2, column=1, sticky="ew")

        # Colors
        frame_col = tk.LabelFrame(self.tab_style, text="Colors", padx=5, pady=5)
        frame_col.pack(fill="x", padx=10, pady=5)

        btn_t_col = tk.Button(frame_col, text="Header Color", bg=GLOBAL_CONFIG['title_color'],
                              command=lambda: self.choose_color('title_color', btn_t_col))
        btn_t_col.pack(fill="x", pady=2)

        btn_r_col = tk.Button(frame_col, text="Username Color", bg=GLOBAL_CONFIG['recent_color'],
                              command=lambda: self.choose_color('recent_color', btn_r_col))
        btn_r_col.pack(fill="x", pady=2)

        btn_o_col = tk.Button(frame_col, text="Video Title Color", bg=GLOBAL_CONFIG['older_color'],
                              command=lambda: self.choose_color('older_color', btn_o_col))
        btn_o_col.pack(fill="x", pady=2)

        # Audio
        frame_audio = tk.LabelFrame(self.tab_style, text="Audio", padx=5, pady=5)
        frame_audio.pack(fill="x", padx=10, pady=5)
        tk.Button(frame_audio, text="Browse Sound", command=self.browse_sound).pack(side="left", padx=5)
        tk.Button(frame_audio, text="Test", command=self.play_sound).pack(side="left", padx=5)

        tk.Button(self.tab_style, text="Apply & Save All", command=self.save_config, bg="#90ee90").pack(fill="x",
                                                                                                        padx=20,
                                                                                                        pady=15)

    # --- SCALING ---
    def on_ctrl_scroll(self, event, manual_delta=None):
        delta = manual_delta if manual_delta else event.delta
        if delta > 0:
            self.current_font_size += 1
        else:
            self.current_font_size -= 1
        self.current_font_size = max(8, min(self.current_font_size, 30))
        self.update_app_fonts()

    def update_app_fonts(self):
        new_font = ("Arial", self.current_font_size)
        title_font = ("Arial", self.current_font_size + 6, "bold")
        style = ttk.Style()
        style.configure('.', font=new_font)

        def update_widget(w):
            try:
                if w == self.lbl_title:
                    w.config(font=title_font)
                else:
                    w.config(font=new_font)
            except:
                pass
            for c in w.winfo_children(): update_widget(c)

        update_widget(self.root)

    # --- LOGIC ---
    def log(self, msg):
        self.root.after(0, lambda: self._log_internal(msg))

    def _log_internal(self, msg):
        self.log_list.insert(0, f"[{time.strftime('%H:%M:%S')}] {msg}")
        self.status_var.set(msg)

    def choose_color(self, config_key, btn_widget):
        curr = GLOBAL_CONFIG.get(config_key, "#ffffff")
        color = colorchooser.askcolor(color=curr, title=f"Choose Color")[1]
        if color:
            GLOBAL_CONFIG[config_key] = color
            btn_widget.config(bg=color)
            self.save_config()

    def set_int_config(self, key, val):
        try:
            GLOBAL_CONFIG[key] = int(val)
            self.save_config()
        except:
            pass

    def browse_sound(self):
        f = filedialog.askopenfilename(filetypes=[("Audio", "*.wav *.mp3")])
        if f: self.sound_path_var.set(f)

    # --- QUEUE & AUDIO PROCESSOR ---
    def _queue_processor(self):
        """Monitors the queue and processes alerts sequentially"""
        while True:
            try:
                # 1. Get next item (blocks until item is available)
                alert_data = REPOST_QUEUE.get()

                # 2. Update Overlay State
                TRACKER_STATE["current_alert"] = alert_data
                TRACKER_STATE["is_visible"] = True

                # 3. Handle Audio & Duration
                audio_path = GLOBAL_CONFIG.get("sound_file", "")
                wait_time = 5.0  # Default wait time if no audio

                if audio_path and os.path.exists(audio_path) and not self.is_muted.get():
                    try:
                        # Load as Sound to get length
                        sound = pygame.mixer.Sound(audio_path)
                        duration = sound.get_length()

                        # Cap at 15 seconds
                        wait_time = min(duration, 15.0)

                        # Play
                        sound.play()
                    except Exception as e:
                        print(f"Audio Error: {e}")

                # 4. Wait for audio to finish (showing the alert)
                time.sleep(wait_time)

                # 5. Add a small buffer for reading the text (e.g., 2 seconds)
                time.sleep(2.0)

                # 6. Hide Alert
                TRACKER_STATE["is_visible"] = False

                # 7. Wait for fade out animation (0.5s CSS transition + buffer)
                time.sleep(1.0)

            except Exception as e:
                print(f"Queue Error: {e}")
                time.sleep(1)

    def play_sound(self):
        # Test function for GUI button
        f = self.sound_path_var.get()
        if f and os.path.exists(f) and not self.is_muted.get():
            try:
                pygame.mixer.Sound(f).play()
            except:
                pass

    def start_browser(self):
        threading.Thread(target=self._init_browser, daemon=True).start()

    def _init_browser(self):
        self.log("Opening Chrome...")
        try:
            opts = uc.ChromeOptions()
            opts.add_argument("--mute-audio")
            self.driver = uc.Chrome(options=opts)
            self.driver.get("https://rumble.com/login.php")
            self.log("Browser Ready. Please Login.")
            self.root.after(0, lambda: self.btn_track.config(state="normal"))
        except Exception as e:
            self.log(f"Browser Error: {e}")

    def toggle_tracking(self):
        if not self.is_tracking:
            self.is_tracking = True
            self.btn_track.config(text="Stop Tracking", bg="#ff9999")

            try:
                self.driver.minimize_window()
            except:
                pass

            threading.Thread(target=self._tracker_loop, daemon=True).start()
        else:
            self.is_tracking = False
            self.btn_track.config(text="Start Tracking", bg="#90ee90")
            self.log("Tracking Stopped.")

    def _tracker_loop(self):
        self.log(f"Tracking Active. Interval: {GLOBAL_CONFIG['poll_interval']}s")
        while self.is_tracking:
            try:
                self.driver.refresh()
                time.sleep(3)

                try:
                    bell_btn = self.driver.find_element(By.CSS_SELECTOR, ".user-notifications--bell-button")
                    self.driver.execute_script("arguments[0].click();", bell_btn)
                    time.sleep(1.5)
                except:
                    self.log("Cannot find notifications. Are you logged in?")
                    time.sleep(5)
                    continue

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                notif_list = soup.find("ul", class_="user-notifications--list")

                if notif_list:
                    items = notif_list.find_all("li")

                    # We collect them in a list first to process order
                    batch_reposts = []

                    for li in items:
                        text_div = li.find("div", class_="user-notifications--text")
                        if not text_div: continue
                        body_div = text_div.find("div", class_="user-notifications--body")
                        if not body_div: continue

                        full_text = body_div.get_text(" ", strip=True)

                        if "reposted your video" in full_text:
                            # Generate Persistent Stable ID
                            n_id = hashlib.md5(full_text.encode('utf-8')).hexdigest()

                            if n_id not in self.seen_reposts:
                                self.seen_reposts.add(n_id)
                                # Save immediately to history
                                self.save_history()

                                user_link = body_div.find("a")
                                user = user_link.text if user_link else "Unknown"

                                vid_title = "Unknown"
                                if '"' in full_text:
                                    parts = full_text.split('"')
                                    if len(parts) > 1: vid_title = parts[1]

                                batch_reposts.append({"user": user, "video": vid_title})
                                self.log(f"NEW REPOST QUEUED: {user}")

                    # Queue oldest first from this batch so they play in order
                    for item in reversed(batch_reposts):
                        REPOST_QUEUE.put(item)

            except Exception as e:
                print(f"Loop Error: {e}")

            time.sleep(int(GLOBAL_CONFIG['poll_interval']))

    def on_close(self):
        self.is_tracking = False
        self.log("Closing Chrome...")
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = RumbleRepostTracker(root)
    root.mainloop()
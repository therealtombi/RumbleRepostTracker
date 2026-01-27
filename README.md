# Rumble Repost Tracker (Pro) 🤖

A professional Python-based application for streamers that tracks reposts on your Rumble channel in real-time. It generates a customizable, animated overlay for OBS/Streamlabs and plays audio alerts when your content is reposted.

![App Screenshot](https://via.placeholder.com/800x450?text=Rumble+Repost+Tracker+Pro)

## 🚀 Features (v3.0)

* **Smart Session Capture:** Logs you in once via a visible browser window, captures your session cookies & user agent, and saves them securely. You don't need to log in every time you run the app.
* **Hidden Background Tracking:** Runs a minimized, resource-optimized browser instance in the background to monitor notifications, ensuring Cloudflare checks are passed successfully.
* **Modern Dark UI:** Built with `CustomTkinter` for a sleek, responsive Windows 11-style interface.
* **Live Style Preview:** Instant feedback in the "Style & Config" tab. Change fonts, colors, and titles, and see them update immediately in the app.
* **Google Fonts Integration:** Select from the top 50 most popular Google Fonts for streamers.
* **Pop-out Web Preview:** Verify exactly how your overlay (and fonts) will render in OBS without needing to launch streaming software.
* **Custom Audio:** Supports `.mp3` and `.wav` alert sounds with smart duration handling (minimum 10s, auto-fade at 20s).

## 🛠️ Prerequisites

* **OS:** Windows 10/11
* **Browser:** A Chromium-based browser must be installed (Google Chrome, Brave, Edge, Opera, or Vivaldi).
* **Python:** 3.10 or newer (if running from source).

## 📦 Installation

### Option A: Running from Source

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/rumble-repost-tracker.git](https://github.com/yourusername/rumble-repost-tracker.git)
    cd rumble-repost-tracker
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Key dependencies: `customtkinter`, `undetected-chromedriver`, `flask`, `pygame`, `beautifulsoup4`, `requests`.*

3.  **Run the application:**
    ```bash
    python rumble_tracker.py
    ```

### Option B: Standalone Executable
If you have built the `.exe` using PyInstaller, simply double-click `RumbleRepostTracker.exe`. No Python installation is required.

## ▶️ How to Use

### 1. Login & Capture
1.  Go to the **"Controls"** tab.
2.  Click **"1. Login & Capture"**. A visible browser window will open.
3.  Log in to your Rumble account manually.
4.  **Wait:** Once the app detects you are logged in (it sees the notification bell), it will automatically save your session and close the window.
5.  The button will turn green and say **"LOGGED IN"**.

### 2. Start Tracking
1.  Click **"2. Start Tracking (Background)"**.
2.  The app will launch a hidden (minimized) browser instance using your saved session.
3.  It will poll your feed every 5 seconds for new "Repost" notifications.

### 3. Setup in OBS
1.  Add a new **Browser Source** in OBS.
2.  **Uncheck** "Local File".
3.  Set URL to: `http://127.0.0.1:5050`
4.  Set Width: `1920` (or your canvas width) and Height: `300`.
5.  **Important:** Check **"Control audio via OBS"** if you want the alert sound to go through your stream mixer.

## 🎨 Customization
* Navigate to the **"Style & Config"** tab.
* **Live Preview:** As you type a new title or select a font, the preview box updates instantly.
* **Fonts:** Pick from the list of 50 Google Fonts. 
    * *Note:* The App Preview uses system fonts. If a Google Font isn't installed on your PC, the preview might default to Arial, but the **OBS Overlay/Web Preview** will always render the correct font from the web.
* **Test:** Click the "Test" button to play the sound and trigger a fake alert on the overlay.

## 🔧 Troubleshooting

**"Login Expired" Warning:**
If your session times out, the app will warn you on startup. Simply click the "LOGGED IN" button (which resets the session) and click "1. Login & Capture" to sign in again.

**Font looking wrong in the App:**
The Tkinter app can only display fonts installed on your Windows machine. To see the *true* rendering, click **"🚀 Pop-out Web Preview"**.

sequenceDiagram
    participant User
    participant GUI as Python App (CTk)
    participant VisibleDriver as Chrome (Visible)
    participant HiddenDriver as Chrome (Minimized)
    participant File as Cookie File (JSON)
    participant Rumble as Rumble.com
    participant Overlay as OBS/Web Source

    box "Phase 1: Authentication" #f9f9f9
    User->>GUI: Click "1. Login & Capture"
    GUI->>VisibleDriver: Launch Browser
    VisibleDriver->>Rumble: User logs in manually
    loop Check Login Status
        VisibleDriver->>Rumble: Check for Bell Icon
        Rumble-->>VisibleDriver: Element Found
    end
    VisibleDriver->>GUI: Success Signal
    GUI->>VisibleDriver: Extract Cookies & User-Agent
    GUI->>File: Save Session Data (JSON)
    GUI->>VisibleDriver: Close Window
    GUI->>GUI: Update Button to "LOGGED IN"
    end

    box "Phase 2: Tracking" #e1f5fe
    User->>GUI: Click "2. Start Tracking"
    GUI->>File: Load Session Data
    GUI->>HiddenDriver: Launch with Saved Cookies
    Note right of HiddenDriver: Window Minimized immediately
    
    loop Every 5 Seconds
        HiddenDriver->>Rumble: Refresh Notification Page
        Rumble-->>HiddenDriver: HTML Content
        HiddenDriver->>GUI: Parse for "Reposted your video"
        
        alt New Repost Detected
            GUI->>Overlay: Update API JSON {user, video, timestamp}
            Overlay->>Overlay: Trigger Animation & Sound
        end
    end
    end

    box "Phase 3: Live Config" #fff3e0
    User->>GUI: Change Font/Color
    GUI->>GUI: Update Global Config
    Overlay->>GUI: Poll /api/data
    GUI-->>Overlay: Return New Config
    Overlay->>Overlay: Instant Re-render
    end


## 📜 License
MIT License

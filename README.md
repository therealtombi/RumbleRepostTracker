# Rumble Repost Tracker 🤖

A Python-based application that tracks reposts on your Rumble channel in real-time and displays them via a custom overlay for OBS/Streamlabs.

![App Screenshot](https://via.placeholder.com/800x400?text=Rumble+Repost+Tracker+Screenshot)

## 🚀 New in v2.0
* **Multi-Browser Support:** Now supports **Google Chrome, Brave, Microsoft Edge, Opera, and Vivaldi** out of the box.
* **Smart Audio Triggers:** Fixed audio sync issues using timestamp validation—alerts will now play reliably in OBS even if you have the dashboard open elsewhere.
* **Graceful Recovery:** The app no longer crashes if the browser window is accidentally closed; it simply pauses tracking.
* **Browser Override:** Manually point to any Chromium-based executable if auto-detection fails.

## ✨ Features
* **Real-time Tracking:** Polls your Rumble notifications feed to detect when someone reposts your content.
* **OBS Overlay:** Generates a transparent, animated HTML overlay that fits seamlessly into your stream.
* **Custom Audio:** Supports `.mp3` and `.wav` alert sounds.
* **Visual Customization:** Change fonts, colors, sizes, and alignment directly from the app.
* **History Tracking:** Remembers previous reposts so you don't get duplicate alerts on restart.

## 🛠️ Prerequisites

* **OS:** Windows 10/11
* **Python:** 3.10 or newer
* **Browser:** A Chromium-based browser (Chrome, Brave, Edge, etc.) installed.

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/rumble-repost-tracker.git](https://github.com/yourusername/rumble-repost-tracker.git)
    cd rumble-repost-tracker
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you are on Linux, you may also need to install `tk` (e.g., `sudo apt-get install python3-tk`).*

## ▶️ Usage

### 1. Configuration
1.  Run the application:
    ```bash
    python rumble_tracker.py
    ```
2.  Go to the **"Style & Config"** tab to set your colors, font, and alert sound.
3.  Go to the **"Controls"** tab.
4.  Select your browser from the dropdown (e.g., "Brave Browser"). If it's not listed, check "Manual Override Path" and find your `.exe`.

### 2. Login
1.  Click **"1. Open Browser & Login"**.
2.  An automated browser window will open. **Log in to your Rumble account manually.**
3.  Minimize the window (do not close it).

### 3. Start Tracking
1.  Click **"2. Start Tracking"**.
2.  The app is now monitoring your feed.

### 4. Setup in OBS
1.  Add a new **Browser Source**.
2.  **Uncheck** "Local File".
3.  Set URL to: `http://127.0.0.1:5050`
4.  Set Width: `600`, Height: `200`.
5.  **Crucial Audio Step:**
    * Double-click the Browser Source -> Check **"Control audio via OBS"**.
    * Go to OBS Audio Mixer -> Click the Gear Icon -> Advanced Audio Properties.
    * Set the Browser Source to **"Monitor and Output"**.

## 🔧 Troubleshooting

**"Invalid Session ID" or Browser Crashes:**
The app now handles this gracefully. If the browser closes, tracking stops. Simply click "Open Browser" to start a new session.

**Audio not playing in OBS:**
Ensure you have set the Audio Monitoring to "Monitor and Output" in OBS Advanced Audio Properties.

**Browser not found:**
Use the "Manual Override" checkbox and browse to your `chrome.exe`, `brave.exe`, or `msedge.exe`.

## 📜 License
[MIT](https://choosealicense.com/licenses/mit/)

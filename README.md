# Rumble Repost Tracker (Pro) 🤖

A professional Python-based application for streamers that tracks reposts on your Rumble channel in real-time. It generates a customizable, animated overlay for OBS/Streamlabs and plays audio alerts when your content is reposted.

## 🚀 Features (v2.1)

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

## 📦 Installation
### Standalone Executable
Download the `.exe` build using PyInstaller from the bottom of the release pages then, simply double-click `RumbleRepostTracker.exe`. No Python installation is required.

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

## 📜 License
MIT License

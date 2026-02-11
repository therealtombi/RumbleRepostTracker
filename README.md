# Rumble Repost Tracker (Pro) v3.0 🤖

**Rumble Repost Tracker** is a professional tool for streamers that monitors your Rumble notifications in real-time. When someone reposts your video, it triggers a fully customizable, animated overlay (for OBS/Streamlabs) and plays an audio alert.

![App Screenshot](https://via.placeholder.com/800x450?text=Rumble+Repost+Tracker+v3.0)

## 🚀 Key Features (v3.0)

* **Smart Session Capture:** Log in once via a visible browser. The app securely saves your session cookies and User-Agent, so you don't have to log in every time.
* **Stealth Tracking:** Runs a hidden, resource-optimized browser instance in the background to bypass Cloudflare protection.
* **Auto-Fix Driver Logic:** Automatically detects if your Chrome version doesn't match the driver and attempts to fix itself instantly. Includes a "Force Version" override for edge cases.
* **Live Style Preview:** Customize fonts, colors, and titles with instant visual feedback in the app.
* **Pop-out Web Preview:** A dedicated button (`🚀`) to verify exactly how Google Fonts and CSS will render on the web/OBS before you go live.
* **Audio Control:** Integrated Volume Slider (0-100%) and Mute toggle.
* **Error Logging System:** A dedicated tab that captures internal errors and allows you to one-click email support or copy logs to the clipboard.

## 🛠️ Prerequisites

1.  **Operating System:** Windows 10 or 11.
2.  **Browser:** **Google Chrome** is highly recommended for the best stability. (Brave, Edge, Opera, and Vivaldi are supported but may require manual path configuration).

## 📦 Installation

### Option A: Standalone Executable (Recommended)
* Download `RumbleRepostTracker.exe`.
* Double-click to launch. No Python installation required.

### Option B: Running from Source
1.  Install Python 3.10+.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run: `python rumble_tracker.py`

## ▶️ User Guide

### Phase 1: Authentication
1.  Go to the **Controls** tab.
2.  Click **"1. Login & Capture"**. A Chrome window will open.
3.  Log in to your Rumble account manually.
4.  **Wait:** As soon as the app detects the "Notification Bell", it saves your session and closes the window automatically.
5.  The button will turn green and read **"LOGGED IN"**.

### Phase 2: Configuration & Style
1.  Go to the **Style & Config** tab.
2.  **Visuals:** Choose from 50+ Google Fonts, change colors, and adjust alignment.
3.  **Audio:** Pick a custom sound and set the **Volume Slider**.
4.  **Preview:**
    * The box in the app shows a rough preview.
    * Click **"🚀 Pop-out Web Preview"** to see the *exact* browser rendering (fonts/animations).

### Phase 3: OBS Setup
1.  In OBS Studio, add a **Browser Source**.
2.  **Uncheck** "Local File".
3.  Set URL to: `http://127.0.0.1:5050`
4.  Set Dimensions to **1920 x 1080** (Width x Height).
5.  Check **"Control audio via OBS"** (allows you to mix the alert volume in OBS).
6.  **Uncheck** "Refresh browser when scene becomes active".

### Phase 4: Go Live
1.  Return to the **Controls** tab.
2.  Click **"2. Start Tracking (Background)"**.
3.  The app will launch a hidden process to monitor your feed every 5 seconds.
4.  Minimize the app and start streaming!

## 🔧 Troubleshooting

### **"Session not created" / Driver Error**
The app now attempts to fix this automatically.
* If it fails, look at the **Controls** tab for the **"Force Driver Version"** box.
* Enter your Chrome Major Version (e.g., `144`) and click **Save**.
* Restart the app.

### **Login Issues**
If you see "Login Expired" or 403 errors in the logs:
1.  Click the Green **"LOGGED IN"** button to reset your session.
2.  Click **"1. Login & Capture"** to sign in again.

### **Reporting Bugs**
1.  Go to the **Error Logs** tab.
2.  Click **"Email Support"**. This will open your email client with the logs pre-attached, addressed to the developer.

## 📄 License
MIT License.
# Rumble Repost Tracker (Pro) v3.2 🤖

**Rumble Repost Tracker** is a professional tool for streamers that monitors your Rumble notifications in real-time. When someone reposts your video, it triggers a fully customizable, animated overlay (for OBS/Streamlabs) and plays an audio alert.

![App Screenshot](https://via.placeholder.com/800x450?text=Rumble+Repost+Tracker+v3.1)

## 🚀 New in v3.2

* **🛡️ Stealth Headless Mode:** The tracking browser now runs **completely invisible** in the background. It will not appear on your taskbar or screen, preventing accidental closures while you are streaming.
* **🚀 Pop-out Web Preview:** A dedicated button to verify exactly how Google Fonts and CSS will render on the web/OBS before you go live.
* **🔊 Volume Mixing:** Integrated Volume Slider (0-100%) that syncs with both the test button and the live overlay.
* **🔧 Auto-Fix Drivers:** Automatically detects if your Chrome version doesn't match the driver and attempts to self-repair.

## 🛠️ Prerequisites

1.  **Operating System:** Windows 10 or 11.
2.  **Browser:** **Google Chrome** is highly recommended. (Brave, Edge, Opera, and Vivaldi are supported).
3.  **Python:** Python 3.10 or newer (if running from source).

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
2.  Click **"1. Login & Capture"**. A **visible** Chrome window will open.
3.  Log in to your Rumble account manually.
4.  **Wait:** As soon as the app detects the "Notification Bell", it automatically saves your session and closes the window.
5.  The button will turn green and read **"LOGGED IN"**.

### Phase 2: Style & Config
1.  Go to the **Style & Config** tab.
2.  **Visuals:** Choose from 50+ Google Fonts, change colors, and adjust alignment.
3.  **Audio:** Pick a custom sound file and set the **Volume Slider**.
4.  **Verify:**
    * The box in the app shows a rough preview.
    * Click **"🚀 Pop-out Web Preview"** to see the *exact* rendering (fonts/animations).

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
3.  **Note:** You will NOT see a browser window open. The app launches a silent background process to monitor your feed.
4.  Minimize the app and start streaming!

## 🔧 Troubleshooting & FAQ

### **"Session not created" / Driver Error**
If Chrome updates in the background, the tracker might crash.
* **Auto-Fix:** The app attempts to fix this automatically on restart.
* **Manual Fix:** Go to the **Controls** tab. In the **"Force Driver Version"** box, type your Chrome major version (e.g., `144`) and click Save. Restart the app.

### **"I clicked Start Tracking but nothing happened?"**
This is normal in **v3.1**. The browser is now "Headless" (invisible). Check the **Error Logs** tab; if it says "Tracking Active", it is working.

### **"Login Expired"**
Cookies eventually expire. If you see this warning:
1.  Click the Green **"LOGGED IN"** button to reset your session.
2.  Click **"1. Login & Capture"** to sign in again.

## 📞 Support

If you encounter persistent issues:
1.  Go to the **Error Logs** tab.
2.  Click **"Email Support"**. This will open your email client with the logs pre-attached, addressed to the developer.

---

## 📄 License
MIT License.

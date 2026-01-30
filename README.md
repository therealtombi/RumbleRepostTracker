# Rumble Repost Tracker (Pro) v3.0 🤖

**Rumble Repost Tracker** is a dedicated tool for streamers that monitors your Rumble notifications in real-time. When someone reposts your video, it triggers a customizable animated overlay (for OBS/Streamlabs) and plays an audio alert, allowing you to thank your supporters instantly.

![App Screenshot](https://via.placeholder.com/800x450?text=Rumble+Repost+Tracker+Pro+Interface)

## 🚀 Key Features

* **Smart Session Capture:** Logs you in securely using a visible browser, captures your session cookies, and stores them locally. You only need to log in once.
* **Stealth Tracking:** Runs a hidden, resource-optimized browser instance in the background to bypass Cloudflare bot protection and 403 errors.
* **OBS Integration:** Hosts a local web server to provide a clean, transparent browser source for your streaming software.
* **Live Style Preview:** Customize colors, titles, and alignment in the app with instant visual feedback.
* **Google Fonts:** Select from the top 50 most popular Google Fonts.
    * *Includes a "Pop-out Web Preview" to verify font rendering exactly as it will appear on stream.*
* **Audio Control:** Built-in volume slider and mute toggle. Audio can be routed through the OBS mixer.
* **Auto-Fix Drivers:** Automatically detects Chrome version mismatches and attempts to self-repair, with a manual override option for stubborn drivers.
* **Error Logging:** Dedicated tab for capturing issues with a direct "Email Support" button.

## 🛠️ Prerequisites

1.  **Operating System:** Windows 10 or 11.
2.  **Browser:** **Google Chrome** is highly recommended. (Brave, Edge, or Opera may work but Chrome is preferred for driver stability).

## 📦 Installation

### Standalone Executable
* Download the `RumbleRepostTracker.exe` from the bottom of this page, simply double-click it to launch. No Python installation is required.

## ▶️ User Guide

### Phase 1: Authentication
1.  Go to the **Controls** tab.
2.  Click **"1. Login & Capture"**. A Chrome window will open.
3.  Log in to your Rumble account manually.
4.  **Wait:** As soon as the app detects the "Notification Bell" inside the browser, it will automatically save your session and close the window.
5.  The button will turn green and read **"LOGGED IN"**.

### Phase 2: Configuration
1.  Go to the **Style & Config** tab.
2.  **Customize:** Change the Title text, Font, Colors, and Alignment.
3.  **Audio:** Select a sound file (`.mp3` or `.wav`) and adjust the **Volume Slider**.
4.  **Preview:**
    * *App Preview:* Shows a rough approximation (uses System Fonts).
    * *Pop-out Preview:* Click **🚀 Pop-out Web Preview** to open a window showing exactly how the HTML/CSS/Google Fonts will look on stream.

### Phase 3: OBS Setup
1.  Open OBS Studio.
2.  Add a **Browser Source**.
3.  **Uncheck** "Local File".
4.  Set the URL to: `http://127.0.0.1:5050`
5.  Set Width: `1920` (or your canvas width) and Height: `300`.
6.  **Recommended:** Check **"Control audio via OBS"** to manage alert volume within your streaming mixer.
7.  **Do NOT** check "Refresh browser when scene becomes active".

### Phase 4: Go Live!
1.  Back in the app's **Controls** tab, click **"2. Start Tracking (Background)"**.
2.  The app will launch a hidden background process to monitor your feed every 5 seconds.
3.  You can minimize the app (do not close it) and start streaming.

## 🔧 Troubleshooting & FAQ

### **"Session not created / Chrome Driver Version Mismatch"**
If Chrome updates in the background, the tracker might crash.
* **Auto-Fix:** The app attempts to fix this automatically on restart.
* **Manual Fix:** Go to the **Controls** tab. In the **"Force Driver Version"** box, type your Chrome major version (e.g., `144`) and click Save. Restart the app.

### **"The font in the App Preview looks basic/wrong"**
The Python app window can only display fonts installed on your Windows system.
* The **OBS Overlay** (and the Pop-out Web Preview) downloads fonts from the internet, so your stream will always look correct even if the app preview looks generic.

### **"Login Expired"**
Cookies eventually expire. If you see this warning:
1.  Click the Green **"LOGGED IN"** button (this resets your session).
2.  Click **"1. Login & Capture"** to sign in again.

### **"Session Blocked (403)"**
If Cloudflare blocks the connection:
* The app will automatically log this in the "Error Logs" tab.
* It will attempt to switch tracking modes automatically.
* If it persists, click "Login & Capture" to refresh your credentials.

## 📞 Support

If you encounter persistent issues:
1.  Go to the **Error Logs** tab.
2.  Click **"Email Support"**.
3.  This will draft an email to `the.real.tombliboos@gmail.com` with your error history attached.

---

## 📄 License
MIT License. Free to use and modify.

---

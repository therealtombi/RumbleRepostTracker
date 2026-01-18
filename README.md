# Rumble Repost Tracker (OBS Overlay) 🚀

A dedicated tool for Rumble streamers to track, alert, and display reposts in real-time on their OBS stream.

This application automates the process of checking your Rumble notifications, filtering for Reposts, playing a custom sound effect, and displaying the alert on a transparent, animated browser source overlay.

## ✨ Features

* **Real-Time Tracking:** Polls Rumble notifications automatically in the background.
* **OBS Integration:** Provides a transparent, flicker-free HTML overlay hosted locally.
* **Queue System:** Handles multiple reposts sequentially (FIFO) so no alert is skipped.
* **Custom Audio:** Supports custom `.wav` or `.mp3` alert sounds.
* **Persistence:** Remembers reposts even if you restart the application (prevents duplicate alerts).
* **Customization:** Change fonts (Google Fonts), colors, sizing, and polling intervals via the GUI.
* **Anti-Bot Detection:** Uses `undetected-chromedriver` to safely navigate Rumble without triggering Cloudflare blocks.

## 🛠️ System Architecture

How the application connects your Browser, the Python Backend, and OBS.

```mermaid
sequenceDiagram
    participant User
    participant GUI as Tkinter GUI
    participant Driver as Chrome Browser
    participant Logic as Python Backend
    participant Flask as Web Server
    participant OBS as OBS Overlay

    User->>GUI: 1. Launch & Click "Open Browser"
    GUI->>Driver: Start Undetected Chrome
    User->>Driver: Manual Login to Rumble
    User->>GUI: 2. Click "Start Tracking"
    
    loop Every X Seconds (Polling)
        Logic->>Driver: Refresh Page & Click Bell
        Driver-->>Logic: Return HTML Source
        Logic->>Logic: Parse BeautifulSoup
        Logic->>Logic: Filter "Reposted your video"
        
        alt New Repost Detected
            Logic->>Logic: Generate Unique ID & Check History
            Logic->>Logic: Add to Alert Queue
            Logic->>Logic: Save to history.json
        end
    end

    par Queue Processor
        loop Every 0.5s
            Logic->>Logic: Check Queue
            alt Item in Queue
                Logic->>Logic: Set Global State (Current Alert)
                Logic->>User: Play Audio Alert
                Logic->>Logic: Wait for Audio Duration
            end
        end
    and Overlay Render
        loop Every 1s
            OBS->>Flask: GET /api/data
            Flask-->>OBS: Return JSON {repost_data, config}
            OBS->>OBS: Update DOM & Animate
        end
    end

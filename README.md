# 👁️ EyeReminder

**EyeReminder** is a lightweight, professional 20-20-20 Eye Health & Hydration assistant for Windows desktop. It monitors active screen time, pauses automatically when idle or locked, and delivers elegant, floating break popups to protect your eyes and maintain optimal workplace ergonomics.

---

## ✨ Features

- **👀 20-20-20 Eye Rest Prompts**: Timed 20-second break popups reminding you to focus on an object 20 feet away every 20 minutes.
- **💧 Hydration Reminders**: Configurable water intake reminders to keep you hydrated throughout the day.
- **🧠 Smart Idle & Lock Detection**: Automatically pauses timer when you step away, lock your PC, or enter quiet hours.
- **🌙 Quiet Hours / Lunch Mode**: Schedule quiet periods (e.g., lunch breaks) during which reminders are suppressed.
- **📊 Daily Statistics & Progress**: Tracks completed eye and water breaks per day with historical logging.
- **⚙️ Full Customization**: Custom break durations, work intervals, audio chimes, and automatic Windows startup.
- **⚡ Ultra Lightweight**: Low CPU usage (< 0.1%) and minimal memory footprint (~35MB RAM).

---

## 📁 Project Structure

```
EyeReminder/
├── assets/                  # Icons and visual branding assets
│   ├── icon.ico
│   └── icon.png
├── src/                     # Source package
│   ├── __init__.py
│   ├── app_controller.py   # Application workflow controller & event loop
│   ├── break_popup.py       # Custom floating popup windows (Eye & Water)
│   ├── config.py            # JSON configuration manager with auto-backup
│   ├── settings_dialog.py   # Qt settings dialog, statistics & about dialog
│   ├── system_utils.py      # Win32 Ctypes idle/lock detection & audio synth
│   └── tray_icon.py         # System tray icon and context menu
├── build_exe.py             # PyInstaller production executable builder
├── generate_assets.py       # Dynamic high-DPI icon generator
├── main.py                  # Entry point with single-instance mutex
├── requirements.txt         # Python dependency specification
└── README.md                # Documentation
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ on Windows 10/11

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py
   ```

---

## 📦 Building Standalone Executable (.exe)

To generate a single-file executable (`EyeReminder.exe`):

```bash
python build_exe.py
```

The output executable will be created in `dist/EyeReminder.exe`.

---

## 📄 License

MIT License. Designed for productivity and personal eye health care.

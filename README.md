# 👁️ EyeReminder

[![Download EyeReminder.exe](https://img.shields.io/badge/Download-EyeReminder.exe-2ea44f?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Vinay9222/Eye-Water-reminder/releases/latest/download/EyeReminder.exe)
[![GitHub Release](https://img.shields.io/github/v/release/Vinay9222/Eye-Water-reminder?style=for-the-badge&color=blue)](https://github.com/Vinay9222/Eye-Water-reminder/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?style=for-the-badge&logo=windows)](https://github.com/Vinay9222/Eye-Water-reminder)

**EyeReminder** is a lightweight, professional 20-20-20 Eye Health & Hydration assistant for Windows desktop. It monitors active screen time, pauses automatically when idle or locked, and delivers elegant, floating break popups to protect your eyes and maintain optimal workplace ergonomics.

---

## 💻 Download & Run (No Installation Required)

For Windows users who want to run EyeReminder instantly without installing Python or setting up code:

### 📥 Direct Download Options:
1. **[Download Latest EyeReminder.exe](https://github.com/Vinay9222/Eye-Water-reminder/releases/latest/download/EyeReminder.exe)** *(Direct Download link from Releases)*
2. **[View All GitHub Releases](https://github.com/Vinay9222/Eye-Water-reminder/releases)** *(Browse release history & release notes)*

### 🚀 How to Run:
1. Download `EyeReminder.exe` using the link above.
2. Double-click **`EyeReminder.exe`** to launch.
3. The app will run quietly in your Windows **System Tray** (near your system clock).
4. Click the system tray icon to open **Settings**, view **Statistics**, or customize your break schedule.

> 💡 *Note: If Windows SmartScreen shows a warning when running for the first time, click **"More Info"** and then **"Run anyway"**.*

---

## ✨ Key Features

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
├── .github/workflows/       # Automated GitHub Actions workflow for building .exe releases
│   └── build-release.yml
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

## 🛠️ Developer Setup & Building from Source

If you want to run or modify the Python source code locally:

### Prerequisites
- Python 3.9+ on Windows 10/11

### Installation & Execution
```bash
# 1. Clone the repository
git clone https://github.com/Vinay9222/Eye-Water-reminder.git
cd Eye-Water-reminder

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run application from source
python main.py
```

### 📦 Building Standalone Executable Manually (.exe)
To compile a single-file `EyeReminder.exe` locally:

```bash
python build_exe.py
```

The output executable will be created in `dist/EyeReminder.exe` and copied to the root directory.

---

## 🏷️ How to Publish a New Executable Download on GitHub

1. Go to your GitHub Repository: `https://github.com/Vinay9222/Eye-Water-reminder`
2. Click on **Releases** > **Draft a new release**.
3. Create a tag (e.g. `v1.0.0`), title it (e.g. `EyeReminder v1.0.0`), and attach `EyeReminder.exe` under **Attach binaries by dropping them here or selecting them**.
4. Click **Publish release**. The download links in the README will automatically point to your newly uploaded `EyeReminder.exe`!

*(Alternatively, pushing a git tag starting with `v` like `v1.0.0` will automatically build and attach the `.exe` via GitHub Actions).*

---

## 📄 License

MIT License. Designed for productivity and personal eye health care.

import os
import sys
import subprocess
import shutil
from generate_assets import create_app_icon


def build():
    print("=== EyeReminder PyInstaller Production Build Script ===")

    workspace = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(workspace, "assets")

    # 1. Ensure icons exist
    icon_png, icon_ico = create_app_icon(assets_dir)

    # 2. Construct PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=EyeReminder",
        "--onefile",
        "--noconsole",
        f"--icon={icon_ico}",
        f"--add-data={icon_png};assets",
        f"--add-data={icon_ico};assets",
        "--clean",
        "main.py"
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=workspace)

    if result.returncode == 0:
        exe_path = os.path.join(workspace, "dist", "EyeReminder.exe")
        print("\n[SUCCESS] BUILD SUCCESSFUL!")
        print(f"Executable location: {exe_path}")

        root_exe = os.path.join(workspace, "EyeReminder.exe")
        try:
            subprocess.run("taskkill /f /im EyeReminder.exe", shell=True, capture_output=True)
            shutil.copy(exe_path, root_exe)
            print(f"Copied to workspace root: {root_exe}")
        except Exception as e:
            print(f"Could not copy to root (file locked): {e}")
            print(f"You can use the built executable at: {exe_path}")
    else:
        print("\n[FAILED] BUILD FAILED! Check PyInstaller output above.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()

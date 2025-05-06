# config.py
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

ADB_PATH         = os.getenv("ADB_PATH", "/mnt/d/platform-tools/adb.exe")
CAPTURE_CMD      = os.getenv("CAPTURE_CMD", "/mnt/c/Windows/System32/cmd.exe")
SHORTCUT_PATH    = os.getenv("SHORTCUT_PATH", "D:\\prsk.lnk")

UI_PARTS_FOLDER  = os.getenv("UI_PARTS_FOLDER", "./ui_parts")
BANNERS_FOLDER   = os.getenv("BANNERS_FOLDER", "./banners")

TEMP_DATA_FILE   = os.getenv("TEMP_DATA_FILE", "./data.json")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "./keys/rock-perception-419201-89a390fa5ca6.json")
SPREADSHEET_KEY  = os.getenv("SPREADSHEET_KEY", "1Kn4dbAOlc4D7w_I6qLQJmm5IFq_uW-jzAmd1T8tmcI")
WORKSHEET_NAME   = os.getenv("WORKSHEET_NAME", "そして針は動き出す")

BASE_DIR = Path(__file__).parent
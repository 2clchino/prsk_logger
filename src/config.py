# config.py
from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")
def load_path(env_var: str, default: str) -> Path:
    """
    環境変数 env_var の値を Path にして返す。
    - 値が絶対パスならそのまま
    - 相対パスなら BASE_DIR/値
    - 未設定なら BASE_DIR/default
    """
    val = os.getenv(env_var)
    if val:
        p = Path(val)
        return p if p.is_absolute() else BASE_DIR / p
    return BASE_DIR / default

ADB_PATH         = os.getenv("ADB_PATH",         "/mnt/d/platform-tools/adb.exe")
CAPTURE_CMD      = os.getenv("CAPTURE_CMD",      "/mnt/c/Windows/System32/cmd.exe")
SHORTCUT_PATH    = os.getenv("SHORTCUT_PATH",    "D:\\prsk.lnk")

UI_PARTS_FOLDER  = load_path("UI_PARTS_FOLDER",  "ui_parts")
BANNERS_FOLDER   = load_path("BANNERS_FOLDER",   "banners")
CONFIG_FILE      = load_path("CONFIG_FILE",      "event_config.yaml")
LAUNCH_FLAG      = load_path("LAUNCH_FLAG",      "launch_flag")
TEMP_DATA_FILE   = load_path("TEMP_DATA_FILE",   "data.json")
CREDENTIALS_FILE = load_path("CREDENTIALS_FILE", "")

SPREADSHEET_KEY  = os.getenv("SPREADSHEET_KEY",  "")
WORKSHEET_NAME   = os.getenv("WORKSHEET_NAME",   "")
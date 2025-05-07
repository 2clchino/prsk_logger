import subprocess
import time
from access_adb import connect_adb
from common import ordered_files, main_prcs, tap_bbox, load_event_config
import time
import datetime
from config import CAPTURE_CMD, SHORTCUT_PATH, UI_PARTS_FOLDER, LAUNCH_FLAG
import os
from dotenv import load_dotenv
from pathlib import Path
import argparse
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
os.chdir(Path(__file__).parent)

def launch_app():
    subprocess.run(
        [CAPTURE_CMD, "/C", "start", "", SHORTCUT_PATH],
        check=True
    )

def reach_goal_state(
    goal_state: str,
    device_serial: str = None,
    folder: str = UI_PARTS_FOLDER,
    delay: float = 1.0,
    retry_duration: float = 180.0
) -> bool:
    _, ordered_names = ordered_files(folder=folder)
    state = None
    while state != goal_state:
        changed = False
        state = main_prcs(ordered_names, device_serial=device_serial, target=goal_state)
        if state != "":
            print(f"state changed → {state}")
            changed=True
            time.sleep(delay)
        if not changed:
            print(f"※どの画像でも state が変わりませんでした。一旦最大 {retry_duration} 秒リトライします。")
            start_time = time.time()
            while time.time() - start_time < retry_duration:
                state = main_prcs(ordered_names, device_serial=device_serial, target=goal_state)
                if state != "":
                    print(f"state changed → {state}")
                    changed=True
                    time.sleep(delay)
                    break
                tap_bbox([0, 0, 0, 0], device_serial=device_serial)
            if not changed:
                print(f"※{retry_duration} 秒以内に state が変化しなかったため、処理を中断します。")
                return False
    print(f"goal_state に到達しました: {goal_state}")
    return True

def is_within_window(now: datetime.datetime,
                     start: datetime.datetime,
                     end:   datetime.datetime) -> bool:
    return start <= now <= end

RETRY_INTERVAL = 10
def main():
    parser = argparse.ArgumentParser(description="アプリ起動スクリプト")
    parser.add_argument(
        '--cron',
        action='store_true',
        help='このフラグがあるときのみ start_time/end_time によるウィンドウチェックを行う'
    )
    args = parser.parse_args()
    if LAUNCH_FLAG.exists():
        LAUNCH_FLAG.unlink()
    if args.cron:
        start_dt, end_dt, _ = load_event_config()
        now = datetime.datetime.now()
        if not is_within_window(now, start_dt, end_dt):
            print(f"[{now}] イベント期間外です: {start_dt} - {end_dt} → 終了します。")
            return
        
    launch_app()
    time.sleep(30)
    now = datetime.datetime.now()
    next_hour = (now + datetime.timedelta(hours=1)).replace(
        minute=0, second=0, microsecond=0
    )
    deadline = next_hour
    while datetime.datetime.now() < deadline:
        try:
            print(f"[{datetime.datetime.now()}] pre_launch を実行します...")
            serial = connect_adb()
            reach_goal_state("02_ranking_button", device_serial=serial)
            LAUNCH_FLAG.touch()
            print(f"[{datetime.datetime.now()}] pre_launch 成功")
            return
        except Exception as e:
            print(f"[{datetime.datetime.now()}] pre_launch 失敗: {e!r}")
            if datetime.datetime.now() + datetime.timedelta(seconds=RETRY_INTERVAL) < deadline:
                print(f" {RETRY_INTERVAL} 秒後に再試行します…")
                time.sleep(RETRY_INTERVAL)
            else:
                print(" 次の 0 分が迫っているため、これ以上リトライしません。")
                break

    print(f"[{datetime.datetime.now()}] pre_launch はタイムアウトしました。")

if __name__ == "__main__":
    main()
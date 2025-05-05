import subprocess
import time
from access_adb import connect_adb
from common import ordered_files, main_prcs, tap_bbox
import time
import datetime
import os
os.chdir(os.path.dirname(__file__))

shortcut = r"D:\\prsk.lnk"
def launch_app():
    subprocess.run(
        ["/mnt/c/Windows/System32/cmd.exe", "/C", "start", "", shortcut],
        check=True
    )

def reach_goal_state(
    goal_state: str,
    device_serial: str = None,
    folder: str = "./ui_parts",
    delay: float = 1.0,
    retry_duration: float = 60.0
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

RETRY_INTERVAL = 10
def main():
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
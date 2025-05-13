#!/usr/bin/env python3
import image_match
import cv2
import os
from typing import Optional, Dict
from access_adb import connect_adb
import time
from extract_digits import ocr_roi
import common
import json 
from record_gspread import record_gspread
from dotenv import load_dotenv
from pathlib import Path
import argparse
import datetime
from config import TEMP_DATA_FILE, BANNERS_FOLDER, LAUNCH_FLAG
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
os.chdir(Path(__file__).parent)

def scroll_center(
    device_serial: Optional[str]     = None,
    start_ratio: float         = 0.6,
    end_ratio: float           = 0.4,
    duration_ms: int           = 300
) -> None:
    """
    画面中央を基準に上下スワイプする。
    
    :param serial:        adb -s で指定するシリアル。None なら defaults 。
    :param start_ratio:   スワイプ開始点の Y 座標（画面高さに対する割合, 0.0-1.0）
    :param end_ratio:     スワイプ終了点の Y 座標（画面高さに対する割合, 0.0-1.0）
    :param duration_ms:   スワイプにかける時間（ミリ秒）
    """
    width, height = 1920, 1080
    x = width // 2
    start_y = int(height * start_ratio)
    end_y   = int(height * end_ratio)

    cmd_args = []
    if device_serial:
        cmd_args += ["-s", device_serial]
    cmd_args += [
        "shell", "input", "swipe",
        str(x), str(start_y),
        str(x), str(end_y),
        str(duration_ms)
    ]
    common.run_adb(cmd_args, device_serial=device_serial)

def record_rank(folder: str = BANNERS_FOLDER, device_serial: Optional[str] = None) -> Dict[int, int]:
    files, ranks = common.ordered_files(folder)
    rank_points: Dict[int, int] = {}
    timeout = 120
    last_progress = time.time()
    try:
        while len(files) > len(rank_points):
            screen = common.capture_screenshot_image(device_serial=device_serial)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            common.save_image_ndarray(image=screen, output_path=f"../screens/{timestamp}.png")
            for rank, name in zip(files, ranks):
                if rank in rank_points:
                    continue
                template = cv2.imread(os.path.join(folder, f"{name}.png"))
                if template is None:
                    continue
                bboxes = image_match.find_template_bboxes(screen, template, 0.9)
                if not bboxes:
                    continue
                for x1, y1, w, h in bboxes:
                    x2, y2 = x1 + w, y1 + h
                    recognized = ocr_roi(screen, [x1, y1, x2, y2])
                    if recognized != str(rank):
                        continue
                    point_bbox = [1320, y1, 1920, y1 + h]
                    point = ocr_roi(screen, point_bbox)
                    if not point.isdigit():
                        continue
                    rank_points[rank] = int(point)
                    last_progress = time.time()
                    break
            if time.time() - last_progress > timeout:
                print(f"[WARN] 3分間進捗がなかったためタイムアウトします。取得済みデータを返します。")
                break
            if 100 in rank_points:
                scroll_center(device_serial=device_serial, start_ratio=0.45, end_ratio=0.4, duration_ms=500)
    except Exception as e:
        print(f"[ERROR] 処理中にエラーが発生しました: {e}。これまでの結果を返します。")
    return rank_points

def stop_app(package_name: str = "com.sega.pjsekai", device_serial: Optional[str] = None):
    """
    ADB 経由で指定アプリを強制終了する: am force-stop
    :returns: 終了に成功すれば True、失敗すれば False
    """
    cmd_args = []
    if device_serial:
        cmd_args += ["-s", device_serial]
    cmd_args += ["shell", "am", "force-stop", package_name]
    common.run_adb(cmd_args, device_serial=device_serial)

def main():
    parser = argparse.ArgumentParser(description="アプリ起動スクリプト")
    parser.add_argument(
        '--cron',
        action='store_true',
        help='このフラグがあるときのみ start_time/end_time によるウィンドウチェックを行う'
    )
    args = parser.parse_args()
    if args.cron:
        if not LAUNCH_FLAG.exists():
            print("launch flag is not exists")
            return 0
    
    _, _, event_name = common.load_event_config()
    serial = connect_adb()
    screen = common.capture_screenshot_image(device_serial=serial)
    common.prcs(screen, "02_ranking_button", device_serial=serial)
    time.sleep(10)
    screen = common.capture_screenshot_image(device_serial=serial)
    common.prcs(screen, "01_highlight_tab", device_serial=serial)
    data = record_rank(device_serial=serial)
    print(data)
    with open(TEMP_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    record_gspread(sheet_name=event_name)
    stop_app(device_serial=serial)
        
if __name__ == '__main__':
    main()
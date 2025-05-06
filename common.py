import subprocess
import image_match
from access_adb import disconnect_offline_devices
import numpy as np
import cv2
import os
from typing import Tuple, Optional, Sequence, List
import re
import time
from config import ADB_PATH, UI_PARTS_FOLDER
import socket

def wait_for_port_close(host: str, port: int, timeout: float = 3.0, interval: float = 0.1):
    """port が LISTEN されなくなるまで待つ"""
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))
                time.sleep(interval)
            except ConnectionRefusedError:
                return True
    return False

def restart_server_and_reconnect(device_serial: str):
    subprocess.run([ADB_PATH, "kill-server"], check=False)
    wait_for_port_close("127.0.0.1", 5037, timeout=3.0)
    
    subprocess.run([ADB_PATH, "start-server"], check=False)
    time.sleep(1)
    try:
        disconnect_offline_devices()
    except Exception as e:
        print(f"[WARN] disconnect_offline_devices(): {e}")
    if ":" in device_serial:
        subprocess.run([ADB_PATH, "connect", device_serial], check=False)
        subprocess.run([ADB_PATH, "-s", device_serial, "wait-for-device"], check=False)

def run_adb(cmd_args, device_serial: str, retries: int = 3, base_delay: float = 1.0):
    """
    adb コマンド実行。失敗したらサーバー再起動→再試行（指数バックオフ）。
    """
    full_cmd = [ADB_PATH] + cmd_args
    for attempt in range(1, retries + 2):
        result = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout
        print(f"[WARN] adb failed (attempt {attempt}/{retries+1}): {result.stderr.strip()}")

        if attempt <= retries:
            restart_server_and_reconnect(device_serial)
            delay = base_delay * (2 ** (attempt - 1))
            print(f"[INFO] retrying after {delay:.1f}s...")
            time.sleep(delay)
        else:
            raise RuntimeError(f"adb command failed after {retries+1} attempts: {full_cmd}")

def main_prcs(parts_image: str = [], device_serial: str = None, target: str = "") -> str:
    screen = capture_screenshot_image(device_serial)
    for img in parts_image:
        if prcs(screen=screen, state=img, device_serial=device_serial, do_tap=img!=target):
            return img
    return ""

def prcs(screen: np.ndarray, state: str, device_serial: str = None, do_tap: bool = True) -> bool:
    tpl = cv2.imread(f"{UI_PARTS_FOLDER}/{state}.png")
    bboxes = image_match.find_template_bboxes(screen, tpl, threshold=0.85)
    if len(bboxes) > 0:
        if do_tap : tap_bbox(bbox=bboxes[0], device_serial=device_serial)
        return True
    return False

def tap_bbox(
    bbox: Tuple[int, int, int, int],
    device_serial: Optional[str] = None
) -> None:
    """
    与えられた bbox（x, y, width, height）の中心を
    adb shell input tap でタップする。

    :param bbox: (x, y, w, h)
    :param device_serial: adb -s で指定するデバイスシリアル（不要なら None）
    """
    x, y, w, h = bbox
    cx = x + w // 2
    cy = y + h // 2

    cmd_args = []
    if device_serial:
        cmd_args += ["-s", device_serial]
    cmd_args += ["shell", "input", "tap", str(cx), str(cy)]

    try:
        run_adb(cmd_args, device_serial=device_serial)
        print(f"Tapped at ({cx}, {cy}) on device {device_serial or 'default'}.")
    except subprocess.CalledProcessError as e:
        print("ADB tap failed:", e)

def ordered_files(folder: str) -> Tuple[List[int], List[str]]:
    files = [
        fname for fname in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, fname))
    ]

    states: List[Tuple[int, str]] = []
    for f in files:
        name = os.path.splitext(f)[0]
        m = re.match(r"^(\d+)", name)
        if m:
            prio = int(m.group(1))
        else:
            prio = 99
        states.append((prio, name))
    states.sort(key=lambda x: x[0])

    prios = [prio for prio, _name in states]
    names = [name for _prio, name in states]
    return prios, names


def capture_screenshot_bytes(device_serial:Optional[str] = None) -> bytes:
    """
    adb exec-out screencap -p を使って PNG バイナリを直接取得し、bytes で返します。
    """
    cmd = [ADB_PATH]
    if device_serial:
        cmd += ["-s", device_serial]
    cmd += ['exec-out', 'screencap', '-p']
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    data, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"screencap failed: {err.decode().strip()}")
    return data

def capture_screenshot_image(device_serial:Optional[str] = None) -> np.ndarray:
    """
    capture_screenshot_bytes() で得た PNG バイナリを
    OpenCV で扱えるnumpy.ndarrayにデコードして返します。
    """
    png_data = capture_screenshot_bytes(device_serial=device_serial)
    arr = np.frombuffer(png_data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode screenshot image")
    return img

def save_image_ndarray(
    image: np.ndarray,
    output_path: str,
    encode_params: Optional[Sequence[int]] = None
) -> None:
    """
    NumPy の ndarray 画像データをファイルに書き出す。

    :param image: H×W×C（BGR）の ndarray 画像
    :param output_path: 保存先のファイルパス (拡張子で形式を自動判別)
    :param encode_params: OpenCV の imwrite に渡すエンコードオプションのリスト
                          例: [cv2.IMWRITE_JPEG_QUALITY, 90] など
    :raises FileNotFoundError: ディレクトリが作成できない場合
    :raises IOError: 書き出しに失敗した場合
    """
    # ディレクトリがなければ作成
    dirpath = os.path.dirname(output_path)
    if dirpath and not os.path.exists(dirpath):
        try:
            os.makedirs(dirpath, exist_ok=True)
        except Exception as e:
            raise FileNotFoundError(f"ディレクトリ作成に失敗: {dirpath}") from e

    # 書き出し
    success = cv2.imwrite(output_path, image, encode_params or [])
    if not success:
        raise IOError(f"画像の書き出しに失敗しました: {output_path}")

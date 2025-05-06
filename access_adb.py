import subprocess
import sys
import time
from config import ADB_PATH

def get_windows_host_ip():
    try:
        proc = subprocess.run(
            ["ip", "route"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        for line in proc.stdout.splitlines():
            if line.startswith("default"):
                parts = line.split()
                if "via" in parts:
                    gw_ip = parts[parts.index("via") + 1]
                    return gw_ip
    except Exception:
        pass
    return "127.0.0.1"

def run_cmd(cmd, check=True):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        print(f"Error running {' '.join(cmd)}:", file=sys.stderr)
        print(result.stderr.decode(), file=sys.stderr)
        sys.exit(1)
    return result.stdout

def ensure_adb_installed():
    if subprocess.run(['which', ADB_PATH], stdout=subprocess.DEVNULL).returncode != 0:
        print("WSL 上に adb が見つかりません。")
        print("  sudo apt update && sudo apt install android-tools-adb")
        sys.exit(1)

def connect_bluestacks(host_ip, port=5555):
    print(f"Connecting to BlueStacks at {host_ip}:{port} ...")
    run_cmd([ADB_PATH, 'connect', f'{host_ip}:{port}'])
    time.sleep(0.5)
    out = run_cmd([ADB_PATH, 'devices'], check=False).decode()
    print("adb devices:\n", out)
    
def get_offline_adb_devices() -> list[str]:
    """
    adb devices の出力から status が 'offline' のシリアル一覧を返す
    """
    out = subprocess.check_output([ADB_PATH, "devices"], text=True)
    offline = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 2 and parts[1] == "offline":
            offline.append(parts[0])
    return offline

def disconnect_offline_devices():
    """
    offline デバイスを adb disconnect で切断
    """
    for serial in get_offline_adb_devices():
        print(f"Disconnecting offline device: {serial}")
        subprocess.run([ADB_PATH, "disconnect", serial], check=False)

def connect_adb():
    disconnect_offline_devices()
    port = 7555
    ensure_adb_installed()
    host_ip = "127.0.0.1"
    connect_bluestacks(host_ip, port=port)
    return f"{host_ip}:{port}"

if __name__ == "__main__":
    connect_adb()
import uuid, time, requests, msgpack, secrets
from Crypto.Cipher import AES

KEY = b"g2fcC0ZczN9MTJ61"
IV  = b"msx3IV0i9XE5uYZ1"
BASE= "https://production-game-api.sekai.colorfulpalette.org/api"

# ---------- 汎用 AES + MsgPack ----------
pad   = lambda b: b + bytes((16-len(b)%16,))*(16-len(b)%16)
unpad = lambda b: b[:-b[-1]]
def enc(obj): return AES.new(KEY, AES.MODE_CBC, IV).encrypt(pad(msgpack.packb(obj)))
def dec(b):   return msgpack.unpackb(unpad(AES.new(KEY, AES.MODE_CBC, IV).decrypt(b)), strict_map_key=False)

# --- 共通ヘッダ定義（Version だけ空で OK） ---
BASE_HDR = {
    "Content-Type":      "application/octet-stream",
    "Accept":            "application/octet-stream",
    "User-Agent":        "UnityPlayer/2019.4.3f1 (UnityWebRequest/1.0)",
    "X-Unity-Version":   "2019.4.3f1",
    "X-Platform":        "Android",              # ← これを忘れると 403
    "X-Device-Model":    "Pixel 8",
    "X-Operating-System":"Android OS 14 / API-34",
    "X-Install-Id": str(uuid.uuid4()),
    "X-GA":         str(uuid.uuid4()),
    "X-MA":         "F8:9A:78:5F:C8:04",
    "X-AI":         secrets.token_hex(16),
}

def get_versions():
    # ▼ X‑Time / X‑Request‑Id も付ける（なくても通るが安全のため）
    hdr = BASE_HDR | {
        "X-Time":       str(int(time.time()*1000)),
        "X-Request-Id": str(uuid.uuid4()),
    }
    r = requests.get(f"{BASE}/system", headers=hdr, timeout=10)
    print(r.status_code, r.headers.get("x-cache"))
    print(r.text[:200])
    r.raise_for_status()
    js = r.json()
    return {
        "app":  js["appVersion"],
        "asset":js["assetbundleVersion"],
        "data": js["masterDataVersion"],
        "res":  js["resourceVersion"],
    }
    
VERS = get_versions()        # ← ここで最新版を都度取得

COMMON = {                   # 毎回コピーして拡張する
    "Content-Type": "application/octet-stream",
    "Accept":        "application/octet-stream",
    "User-Agent":    "UnityPlayer/2019.4.3f1",
    "X-Unity-Version": "2019.4.3f1",
    "X-Platform":    "Android",
    "X-App-Version": VERS["app"],
    "X-Asset-Version": VERS["asset"],
    "X-Data-Version": VERS["data"],
    "X-Resource-Version": VERS["res"],
    "X-Device-Model": "Pixel 8",
    "X-Operating-System": "Android OS 14 / API-34",
}

def call(path, method="GET", body=None, token=None):
    h = COMMON.copy()
    h["X-Request-Id"] = str(uuid.uuid4())
    h["X-Time"] = str(int(time.time()*1000))
    if token:
        h["X-Session-Token"] = token
    data = None if body is None else enc(body)
    r = requests.request(method, BASE + path, headers=h, data=data, timeout=10)
    r.raise_for_status()
    return dec(r.content) if r.content else None

# ---------- ① Guest Registration ----------
reg = call("/user", "POST", {
    "platform":        COMMON["X-Platform"],
    "deviceModel":     COMMON["X-Device-Model"],
    "operatingSystem": COMMON["X-Operating-System"],
})
uid, cred = reg["userRegistration"]["userId"], reg["credential"]

# ---------- ② Login ----------
tok = call(f"/user/{uid}/auth?refreshUpdatedResources=false",
           "PUT", {"credential": cred})["sessionToken"]

# ---------- ③ Ranking ----------
evt_id, rank_key = 250, 100
rk = call(f"/user/{uid}/eventRankings/list?eventId={evt_id}&targetRank={rank_key}",
          token=tok)["eventRankings"][0]
print(f'T{rank_key}: {rk["score"]:,} pt  ({rk["aggregatedAt"]})')
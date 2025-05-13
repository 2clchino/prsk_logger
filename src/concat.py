import cv2
import glob, os
import numpy as np
import pytesseract
from pytesseract import Output

def detect_rank_positions(img):
    # 数字だけ読み取り（例: 100,200…のラベル検出用）
    cfg = "--psm 7 -c tessedit_char_whitelist=0123456789"
    data = pytesseract.image_to_data(img, config=cfg, output_type=Output.DICT)
    pos = {}
    for txt, l, t, w, h in zip(data['text'], data['left'], data['top'], data['width'], data['height']):
        if txt.isdigit():
            val = int(txt)
            if val % 100 == 0:
                pos[val] = (l, t, w, h)
    return pos

def stitch_by_rows(folder, pattern, output_path):
    # 1) 画像読み込み＆行番号位置検出
    paths = sorted(glob.glob(os.path.join(folder, pattern)))
    if not paths:
        raise FileNotFoundError("画像が見つかりません: " + pattern)
    imgs = [cv2.imread(p) for p in paths]
    all_pos = [detect_rank_positions(im) for im in imgs]

    # 2) 全行番号の総集合
    all_ranks = sorted({r for pos in all_pos for r in pos.keys()})

    # 3) 行高さを中央値で決定
    heights = [h for pos in all_pos for (_,_,_,h) in pos.values()]
    row_h = int(np.median(heights))

    # 4) キャンバス準備
    canvas_h = row_h * len(all_ranks)
    canvas_w = max(im.shape[1] for im in imgs)
    canvas = 255 * np.ones((canvas_h, canvas_w, 3), dtype=np.uint8)

    # 5) 行ごとに切り出して貼り付け
    y_off = 0
    for rank in all_ranks:
        for img, pos in zip(imgs, all_pos):
            if rank in pos:
                _, top, _, _ = pos[rank]
                row = img[top:top+row_h, :canvas_w]
                # 足りなければ下／右を白パディング
                h, w = row.shape[:2]
                if h < row_h or w < canvas_w:
                    row = cv2.copyMakeBorder(row,
                                             0, row_h-h,
                                             0, canvas_w-w,
                                             cv2.BORDER_CONSTANT,
                                             value=(255,255,255))
                canvas[y_off:y_off+row_h] = row
                break
        y_off += row_h

    # 6) 保存
    cv2.imwrite(output_path, canvas)
    print(f"✓ 保存しました: {output_path}")

if __name__ == "__main__":
    stitch_by_rows("../screens/", "20250508_19*.png", "stitched.png")
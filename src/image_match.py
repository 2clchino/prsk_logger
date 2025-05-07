import cv2
import numpy as np
from typing import List, Tuple, Union

ImageInput = Union[str, bytes, np.ndarray]

def _load_image(src: ImageInput) -> np.ndarray:
    """
    ImageInput を受け取り、BGR の numpy.ndarray に変換して返す。
    - str: ファイルパスとして cv2.imread()
    - bytes: メモリ上の PNG/JPEG bytes としてデコード
    - np.ndarray: そのまま返す（要 BGR 画像）
    """
    if isinstance(src, np.ndarray):
        return src
    if isinstance(src, bytes):
        arr = np.frombuffer(src, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("バイト列から画像をデコードできませんでした")
        return img
    if isinstance(src, str):
        img = cv2.imread(src)
        if img is None:
            raise FileNotFoundError(f"画像ファイルが読み込めません: {src}")
        return img
    raise TypeError(f"Unsupported image input type: {type(src)}")

def find_template_bboxes(
    screenshot: ImageInput,
    template: ImageInput,
    threshold: float = 0.8
) -> List[Tuple[int, int, int, int]]:
    """
    screenshot 上から template を探し、
    マッチ度 >= threshold の全領域の (x, y, w, h) を返す。

    :param screenshot: ファイルパス／bytes／ndarray
    :param template:    ファイルパス／bytes／ndarray
    :param threshold:   マッチングの閾値 (0～1)
    :return: 見つかった領域 [(x, y, width, height), ...]
    :raises ValueError: マッチしなかった場合
    """
    img = _load_image(screenshot)
    tpl = _load_image(template)

    # テンプレートマッチング
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(res >= threshold)
    h, w = tpl.shape[:2]
    if len(xs) == 0:
        return []

    # (x, y, w, h) のリストを作成
    return [(int(x), int(y), w, h) for x, y in zip(xs, ys)]

def annotate_image_with_bboxes(
    image_path: str,
    bboxes: List[Tuple[int, int, int, int]],
    output_path: str,
    color: Tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2
) -> None:
    """
    画像に対して与えられた bbox を描画し、ファイル保存する。

    :param image_path: 元画像のパス
    :param bboxes: [(x, y, w, h), ...] のリスト
    :param output_path: 保存先パス
    :param color: BGR カラー (デフォルト: 赤)
    :param thickness: 線の太さ (デフォルト: 2)
    :raises FileNotFoundError: 画像が読めない場合
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"画像が見つかりません: {image_path}")

    for (x, y, w, h) in bboxes:
        top_left = (x, y)
        bottom_right = (x + w, y + h)
        cv2.rectangle(img, top_left, bottom_right, color, thickness)

    cv2.imwrite(output_path, img)
    print(f"{len(bboxes)} 件の bbox を描画して {output_path} に保存しました。")

if __name__ == "__main__":
    # 1) 探索して bbox を取得
    bboxes = find_template_bboxes(
        screenshot_path="bluestacks_screen.png",
        template_path="./ui_parts/event_button.png",
        threshold=0.85
    )

    # 2) 描画して保存
    annotate_image_with_bboxes(
        image_path="bluestacks_screen.png",
        bboxes=bboxes,
        output_path="annotated.png"
    )
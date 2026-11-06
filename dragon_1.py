from pathlib import Path
import cv2
import numpy as np

def read_image_utf8(path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Не удалось прочитать: {path.name}")
    return img

def write_image_utf8(path: Path, img):
    ext = path.suffix
    success, encoded = cv2.imencode(ext, img)
    if not success:
        raise IOError(f"Не удалось сохранить: {path.name}")
    encoded.tofile(str(path))

def find_source_image(directory: Path) -> Path:
    valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
    candidates = [
        f for f in directory.iterdir()
        if f.is_file()
           and f.suffix.lower() in valid_exts
           and not f.name.startswith("coin_depth")
    ]
    if not candidates:
        raise FileNotFoundError(f"Файлы изображений не найдены в {directory}")
    for c in candidates:
        if any(k in c.name.lower() for k in ["coin_front", "smartselect", "dragon"]):
            return c
    return candidates[0]

def generate_heightmap():
    script_dir = Path(__file__).resolve().parent
    src_path = find_source_image(script_dir)
    dst_path = script_dir / "coin_depth.png"

    print(f"[+] Обработка: {src_path.name}")
    img = read_image_utf8(src_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Мягкая фильтрация шума
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # 2. Локальный контраст для рельефа деталей
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # 3. Умная маска фона: отсекаем только черный фон, сохраняя все рога и шипы
    # Любой пиксель светлее порогового значения считается частью монеты
    _, alpha_mask = cv2.threshold(gray, 18, 255, cv2.THRESH_BINARY)

    # Закрываем возможные темные разрывы внутри монеты
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    alpha_mask = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kernel)

    # Применяем маску силуэта без искусственной обрезки по кругу
    heightmap = cv2.bitwise_and(enhanced, enhanced, mask=alpha_mask)

    write_image_utf8(dst_path, heightmap)
    print(f"[+] Готово! Все шипы и рога сохранены в {dst_path.name}")

if __name__ == "__main__":
    generate_heightmap()
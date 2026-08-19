from PIL import Image

GRID_MAP = {
    "Hợi": (3, 3), "Tý": (2, 3), "Sửu": (1, 3), "Dần": (0, 3),
    "Mão": (0, 2), "Thìn": (0, 1), "Tị": (0, 0), "Ngọ": (1, 0),
    "Mùi": (2, 0), "Thân": (3, 0), "Dậu": (3, 1), "Tuất": (3, 2),
}


def uploaded_file_to_image(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        image.load()
        return image.convert("RGB"), None
    except Exception as exc:
        return None, f"Không thể đọc ảnh: {exc}"


def crop_12_cung(img, top_cut=0, bottom_cut=3, side_cut=0, overlap_px=15):
    if img is None:
        return {}
    width, height = img.size
    left = width * side_cut / 100
    right = width * (1 - side_cut / 100)
    top = height * top_cut / 100
    bottom = height * (1 - bottom_cut / 100)
    ws = max(1, right - left) / 4
    hs = max(1, bottom - top) / 4
    crops = {}
    for branch, (col, row) in GRID_MAP.items():
        x1 = max(0, int(left + col * ws - overlap_px))
        y1 = max(0, int(top + row * hs - overlap_px))
        x2 = min(width, int(left + (col + 1) * ws + overlap_px))
        y2 = min(height, int(top + (row + 1) * hs + overlap_px))
        if x2 > x1 and y2 > y1:
            crops[branch] = img.crop((x1, y1, x2, y2))
    return crops

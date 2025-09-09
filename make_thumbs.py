# make_thumbs.py
from pathlib import Path
from PIL import Image

DATA_DIR = Path("src/data")       # 원본 이미지 폴더
OUT_DIR = DATA_DIR / "thumb"      # 썸네일 저장 폴더
OUT_DIR.mkdir(exist_ok=True)

for p in DATA_DIR.glob("*.*"):
    if p.is_file():
        try:
            img = Image.open(p).convert("RGB")
            img.thumbnail((640, 640))  # 최대 크기 640px
            out_path = OUT_DIR / (p.stem + ".webp")
            img.save(out_path, format="WEBP", quality=80, method=6)
            print("저장 완료:", out_path)
        except Exception as e:
            print("변환 실패:", p, e)

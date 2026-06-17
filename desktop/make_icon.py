"""
生成 ParaJudge 桌面端图标（PNG → ICO）。

如果已有 .ico 文件请删除本脚本或注释掉主程序。
"""
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed, skip")
    raise SystemExit(0)


def make_icon(size: int = 256) -> Image.Image:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 渐变背景圆形（紫色 → 蓝色）
    for r in range(size // 2, 0, -1):
        t = r / (size / 2)
        # 紫色 (#5b4fcf) → 蓝色 (#00d4ff)
        cr = int(0x5b + (0x00 - 0x5b) * t)
        cg = int(0x4f + (0xd4 - 0x4f) * t)
        cb = int(0xcf + (0xff - 0xcf) * t)
        draw.ellipse(
            [(size // 2 - r, size // 2 - r), (size // 2 + r, size // 2 + r)],
            fill=(cr, cg, cb, 255),
        )

    # 天平符号
    cx, cy = size // 2, size // 2
    # 中线
    draw.line([(cx, cy - size // 4), (cx, cy + size // 4)], fill='white', width=size // 32)
    # 顶横
    draw.line([(cx - size // 3, cy - size // 4), (cx + size // 3, cy - size // 4)],
              fill='white', width=size // 32)
    # 顶珠
    draw.ellipse([(cx - size // 16, cy - size // 4 - size // 16),
                  (cx + size // 16, cy - size // 4 + size // 16)],
                 fill='white')
    # 左盘
    draw.arc([(cx - size // 3, cy - size // 4),
              (cx - size // 6, cy + size // 8)],
             start=200, end=340, fill='white', width=size // 32)
    # 右盘
    draw.arc([(cx + size // 6, cy - size // 4),
              (cx + size // 3, cy + size // 8)],
             start=200, end=340, fill='white', width=size // 32)

    return img


def main():
    out_dir = Path(__file__).parent / "assets"
    out_dir.mkdir(exist_ok=True)
    png_path = out_dir / "icon.png"
    ico_path = out_dir / "icon.ico"

    img = make_icon(256)
    img.save(png_path)
    # ICO 包含多尺寸
    img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Generated: {png_path}")
    print(f"Generated: {ico_path}")


if __name__ == "__main__":
    main()

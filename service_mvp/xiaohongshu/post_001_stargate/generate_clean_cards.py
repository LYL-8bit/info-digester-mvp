from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).resolve().parent / "clean_cards"
OUT_DIR_V2 = Path(__file__).resolve().parent / "clean_cards_v2"
W, H = 1242, 1660
BG = "#fbfaf5"
INK = "#3f3d3b"
MUTED = "#77736d"
LIGHT = "#f3ead8"
YELLOW = "#f5df50"
RED = "#ff2d55"

FONT_BOLD = "C:/Windows/Fonts/simhei.ttf"
FONT_REG = "C:/Windows/Fonts/Deng.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        if text_width(draw, trial, fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def draw_brand(draw: ImageDraw.ImageDraw, page: str) -> None:
    draw.text((92, 86), "BytePulse｜海外AI笔记", font=font(30, True), fill=MUTED)
    draw.text((92, H - 108), page, font=font(26), fill=MUTED)
    draw.text((W - 292, H - 108), "评论「工具」", font=font(30, True), fill=RED)


def draw_quote_mark(draw: ImageDraw.ImageDraw) -> None:
    draw.text((130, 250), "“", font=font(148, True), fill=LIGHT)


def draw_highlight(draw: ImageDraw.ImageDraw, x: int, y: int, width: int) -> None:
    draw.rectangle((x, y, x + width, y + 20), fill=YELLOW)


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    fnt: ImageFont.FreeTypeFont,
    fill: str = INK,
    line_gap: int = 24,
    max_width: int = 980,
) -> int:
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def make_card_1() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "01 / 05")
    draw_quote_mark(draw)
    x, y = 150, 690
    big = font(82, True)
    for line in ["我把 42 分钟", "英文 AI 视频", "整理成了中文笔记"]:
        draw.text((x, y), line, font=big, fill=INK)
        if "英文 AI" in line:
            draw_highlight(draw, x + 250, y + 88, 390)
        y += 132
    draw.text((150, 1135), "OpenAI Stargate 数据中心讲了什么？", font=font(40), fill=MUTED)
    draw.rectangle((150, 1248, 700, 1312), outline=LIGHT, width=3)
    draw.text((176, 1260), "英文 YouTube -> 中文 Markdown", font=font(30, True), fill=INK)
    return im


def make_card_1_v2() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "01 / 05")
    draw_quote_mark(draw)
    x, y = 150, 640
    big = font(94, True)
    for line in ["我把 42 分钟", "英文 AI 视频", "整理成中文笔记"]:
        draw.text((x, y), line, font=big, fill=INK)
        if "AI" in line:
            draw_highlight(draw, x + 380, y + 104, 280)
        y += 148
    draw.text((150, 1165), "OpenAI Stargate 数据中心讲了什么？", font=font(42, True), fill=MUTED)
    return im


def make_card_2() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "02 / 05")
    draw_quote_mark(draw)
    draw.text((150, 560), "一句话总结", font=font(56, True), fill=INK)
    draw_highlight(draw, 150, 640, 310)
    draw_multiline(
        draw,
        "Stargate 是已动工的巨额 AI 算力基建，旨在突破物理极限争夺 AGI。",
        (150, 760),
        font(58, True),
        max_width=930,
        line_gap=30,
    )
    draw_multiline(
        draw,
        "这不是普通 AI 新闻，而是 AI 从软件竞赛走向基础设施竞赛的现场样本。",
        (150, 1165),
        font(36),
        fill=MUTED,
        max_width=880,
    )
    return im


def make_card_2_v2() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "02 / 05")
    draw_quote_mark(draw)
    draw.text((150, 455), "一句话总结", font=font(62, True), fill=INK)
    draw_highlight(draw, 150, 544, 340)
    big = font(72, True)
    y = 710
    for line in ["Stargate 不是", "普通 AI 新闻", "而是一场", "物理基建竞赛"]:
        draw.text((150, y), line, font=big, fill=INK)
        y += 112
    return im


def make_card_3() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "03 / 05")
    draw.text((150, 370), "是否值得看？", font=font(66, True), fill=INK)
    draw.text((150, 535), "4 / 5", font=font(116, True), fill=INK)
    draw_highlight(draw, 155, 655, 275)
    draw_multiline(
        draw,
        "值得。它展示了 AI 背后的真实物理成本：算力、电力、冷却、土地、供应链，以及地方政府的现实博弈。",
        (150, 820),
        font(50, True),
        max_width=930,
        line_gap=28,
    )
    return im


def make_card_3_v2() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "03 / 05")
    draw.text((150, 355), "是否值得看？", font=font(70, True), fill=INK)
    draw.text((150, 535), "4 / 5", font=font(150, True), fill=INK)
    draw_highlight(draw, 155, 695, 340)
    body = font(58, True)
    y = 900
    for line in ["值得。它讲清了", "AI 背后的真实成本：", "算力、电力、冷却、", "土地和供应链。"]:
        draw.text((150, y), line, font=body, fill=INK)
        y += 92
    return im


def make_card_4() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "04 / 05")
    draw.text((150, 280), "我整理出的", font=font(56, True), fill=INK)
    draw.text((150, 360), "4 个核心观点", font=font(72, True), fill=INK)
    draw_highlight(draw, 505, 448, 430)
    items = [
        "软件瓶颈正在变成物理瓶颈",
        "AI 数据中心开始逐电而居",
        "AI 基建像下一代超级公路",
        "碳中和承诺正被算力需求冲击",
    ]
    y = 610
    for idx, item in enumerate(items, 1):
        draw.text((150, y), f"{idx}.", font=font(52, True), fill=RED)
        y = draw_multiline(draw, item, (230, y - 4), font(50, True), max_width=810, line_gap=20)
        y += 46
    return im


def make_card_4_v2() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "04 / 05")
    draw.text((150, 250), "我整理出的", font=font(62, True), fill=INK)
    draw.text((150, 340), "4 个核心观点", font=font(86, True), fill=INK)
    draw_highlight(draw, 485, 450, 500)
    items = [
        "软件瓶颈变成物理瓶颈",
        "AI 数据中心开始逐电而居",
        "AI 基建像下一代超级公路",
        "碳中和承诺被算力需求冲击",
    ]
    y = 650
    for idx, item in enumerate(items, 1):
        draw.text((150, y), f"{idx}.", font=font(62, True), fill=RED)
        y = draw_multiline(draw, item, (240, y - 6), font(58, True), max_width=790, line_gap=18)
        y += 58
    return im


def make_card_5() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "05 / 05")
    draw.text((150, 285), "你发 YouTube 链接", font=font(58, True), fill=INK)
    draw.text((150, 370), "我整理成中文笔记", font=font(70, True), fill=INK)
    draw_highlight(draw, 150, 460, 520)
    items = ["一句话总结 / 是否值得看", "核心观点 / 详细学习笔记", "术语解释 / 行动清单", "Markdown 文件"]
    y = 640
    for item in items:
        draw.ellipse((150, y + 18, 170, y + 38), fill=RED)
        draw.text((205, y), item, font=font(46, True), fill=INK)
        y += 105
    draw.rounded_rectangle((150, 1180, 590, 1286), radius=12, fill=RED)
    draw.text((198, 1207), "评论「工具」", font=font(44, True), fill="white")
    draw.text((150, 1360), "目前先人工处理少量英文 AI/技术视频", font=font(34), fill=MUTED)
    return im


def make_card_5_v2() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    draw_brand(draw, "05 / 05")
    draw.text((150, 330), "你发 YouTube 链接", font=font(66, True), fill=INK)
    draw.text((150, 430), "我整理成中文笔记", font=font(80, True), fill=INK)
    draw_highlight(draw, 150, 530, 610)
    items = ["是否值得看", "核心观点", "详细笔记", "术语解释", "行动清单", "Markdown 文件"]
    y = 705
    for index, item in enumerate(items):
        col = 150 if index % 2 == 0 else 620
        row_y = y + (index // 2) * 115
        draw.ellipse((col, row_y + 20, col + 22, row_y + 42), fill=RED)
        draw.text((col + 48, row_y), item, font=font(44, True), fill=INK)
    draw.rounded_rectangle((150, 1200, 660, 1318), radius=12, fill=RED)
    draw.text((205, 1230), "评论「工具」", font=font(52, True), fill="white")
    return im


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cards = [make_card_1(), make_card_2(), make_card_3(), make_card_4(), make_card_5()]
    for index, image in enumerate(cards, 1):
        image.save(OUT_DIR / f"post_001_card_{index}.png", quality=95)
        print(f"saved: {OUT_DIR / f'post_001_card_{index}.png'}")

    OUT_DIR_V2.mkdir(parents=True, exist_ok=True)
    cards_v2 = [make_card_1_v2(), make_card_2_v2(), make_card_3_v2(), make_card_4_v2(), make_card_5_v2()]
    for index, image in enumerate(cards_v2, 1):
        image.save(OUT_DIR_V2 / f"post_001_card_{index}.png", quality=95)
        print(f"saved: {OUT_DIR_V2 / f'post_001_card_{index}.png'}")


if __name__ == "__main__":
    main()

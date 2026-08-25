#!/usr/bin/env python3
"""Audit core DOCX invariants using only Python's standard library."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
V = "{urn:schemas-microsoft-com:vml}"


def text_of(node: ET.Element) -> str:
    return "".join((t.text or "") for t in node.iter(W + "t")).strip()


def paragraph_style_id(p: ET.Element) -> str:
    ppr = p.find(W + "pPr")
    style = None if ppr is None else ppr.find(W + "pStyle")
    return "" if style is None else style.get(W + "val", "")


def style_names(styles_root: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for style in styles_root.findall(W + "style"):
        sid = style.get(W + "styleId", "")
        name = style.find(W + "name")
        result[sid] = "" if name is None else name.get(W + "val", "")
    return result


def heading_level(style_name: str) -> int | None:
    normalized = style_name.replace(" ", "").lower()
    match = re.fullmatch(r"(?:heading|标题)([1-9])", normalized)
    return None if match is None else int(match.group(1))


def has_picture(p: ET.Element) -> bool:
    return any(
        p.find(".//" + tag) is not None
        for tag in (W + "drawing", W + "pict", W + "object", A + "blip", V + "imagedata")
    )


def is_single_spaced(p: ET.Element) -> bool:
    ppr = p.find(W + "pPr")
    spacing = None if ppr is None else ppr.find(W + "spacing")
    if spacing is None:
        return False
    return spacing.get(W + "lineRule", "auto") == "auto" and spacing.get(W + "line") in {"240", None}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计模板化技术报告 DOCX")
    parser.add_argument("docx", type=Path)
    parser.add_argument("--max-heading-level", type=int, required=True, choices=range(1, 6))
    parser.add_argument("--company", default="", help="Required footer text; empty disables this check")
    parser.add_argument("--allow-header-images", action="store_true")
    parser.add_argument(
        "--page-size-twips",
        default="",
        metavar="WIDTH,HEIGHT",
        help="Expected page size in twips, for example 11906,16838 for A4 portrait",
    )
    parser.add_argument(
        "--margins-twips",
        default="",
        metavar="TOP,BOTTOM,LEFT,RIGHT",
        help="Expected margins in twips",
    )
    return parser.parse_args()


def parse_twips(value: str, count: int, option: str) -> tuple[str, ...] | None:
    if not value:
        return None
    parts = tuple(part.strip() for part in value.split(","))
    if len(parts) != count or any(not part.isdigit() for part in parts):
        raise SystemExit(f"{option} must contain {count} comma-separated non-negative integers")
    return parts


def main() -> int:
    args = parse_args()
    path = args.docx.expanduser().resolve()
    errors: list[str] = []
    expected_size = parse_twips(args.page_size_twips, 2, "--page-size-twips")
    expected_margins = parse_twips(args.margins_twips, 4, "--margins-twips")

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        if not {"word/document.xml", "word/styles.xml"}.issubset(names):
            raise SystemExit("不是有效的 Word DOCX 文件")

        document = ET.fromstring(zf.read("word/document.xml"))
        styles = style_names(ET.fromstring(zf.read("word/styles.xml")))
        counts = {level: 0 for level in range(1, 6)}
        excessive: list[str] = []
        bad_picture_spacing = 0

        for p in document.iter(W + "p"):
            txt = text_of(p)
            level = heading_level(styles.get(paragraph_style_id(p), paragraph_style_id(p)))
            if level is not None:
                counts[level] += 1
                if level > args.max_heading_level:
                    excessive.append(f"标题{level}: {txt[:50]}")
            if has_picture(p) and not is_single_spaced(p):
                bad_picture_spacing += 1

        if excessive:
            errors.append("存在超过指定最高级别的标题: " + "; ".join(excessive[:8]))
        if bad_picture_spacing:
            errors.append(f"有 {bad_picture_spacing} 个图片段落未显式设为单倍行距")

        header_picture_count = 0
        for name in names:
            if re.fullmatch(r"word/header\d+\.xml", name):
                root = ET.fromstring(zf.read(name))
                header_picture_count += sum(
                    1
                    for tag in (W + "drawing", W + "pict", W + "object", A + "blip", V + "imagedata")
                    for _ in root.iter(tag)
                )
        if header_picture_count and not args.allow_header_images:
            errors.append(f"页眉中仍存在 {header_picture_count} 个图片对象")

        footer_text = "".join(
            text_of(ET.fromstring(zf.read(name)))
            for name in names
            if re.fullmatch(r"word/footer\d+\.xml", name)
        )
        if args.company and args.company not in footer_text:
            errors.append(f"页脚未找到“{args.company}”")

        sect = document.find(".//" + W + "sectPr")
        if sect is not None:
            size = sect.find(W + "pgSz")
            margin = sect.find(W + "pgMar")
            if expected_size and (
                size is None or (size.get(W + "w"), size.get(W + "h")) != expected_size
            ):
                errors.append(f"页面尺寸与期望值 {','.join(expected_size)} 不一致")
            if expected_margins:
                expected = dict(zip(("top", "bottom", "left", "right"), expected_margins))
                for key, value in expected.items():
                    if margin is None:
                        errors.append("文档未设置页边距")
                        break
                    if margin.get(W + key) != value:
                        errors.append(f"页边距 {key} 与期望值 {value} 不一致")

        media_count = sum(1 for name in names if name.startswith("word/media/") and not name.endswith("/"))

    print("标题统计: " + ", ".join(f"标题{k}={v}" for k, v in counts.items() if v))
    print(f"指定最高标题级别: {args.max_heading_level}")
    print("图片段落单倍行距: " + ("通过" if not bad_picture_spacing else "不通过"))
    print("页眉图片: " + str(header_picture_count))
    print(f"媒体文件: {media_count}")
    print("页脚公司名称: " + ("通过" if not args.company or args.company in footer_text else "不通过"))

    if errors:
        print("\n审计未通过：")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\n审计通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
